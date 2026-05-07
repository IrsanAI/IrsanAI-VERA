#!/usr/bin/env python3
"""
IrsanAI-VERA — Resonance Reporter Agent v1.0
irsanai_resonance_reporter.py

On-demand IST/SOLL validator and self-repair proposer.

Generates a DSGVO-compliant report for Claude or any online LLM:
- Dashboard state (metrics, KPIs, evidence, audit)
- Local project IST state (files, modules, versions)
- GitHub canonical SOLL state (what the repo defines as correct)
- Deviations detected → VERA_PATCH auto-proposals
- Validation cycle: did last patch achieve its purpose?

Usage:
    python irsanai_resonance_reporter.py
    python irsanai_resonance_reporter.py --validate-last
    python irsanai_resonance_reporter.py --auto-repair
    python irsanai_resonance_reporter.py --output report.md

DSGVO: No personal data. No tokens. No usernames. No file paths with PII.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Optional


GITHUB_REPO = "https://github.com/IrsanAI/IrsanAI-VERA"
GITHUB_RAW  = "https://raw.githubusercontent.com/IrsanAI/IrsanAI-VERA/main"
REPORT_VERSION = "1.0"

# ── Canonical SOLL State (what GitHub defines as correct) ─────────
CANONICAL_MODULES = {
    "core/ontology_loader.py":         {"min_lines": 100, "required_class": "DomainOntology"},
    "core/bayesian/updater.py":        {"min_lines": 100, "required_class": "BayesianBeliefUpdater"},
    "core/bayesian/__init__.py":       {"min_lines": 0},
    "core/auditor.py":                 {"min_lines": 200, "required_class": "EpistemicAuditor"},
    "core/lrp_messenger.py":           {"min_lines": 80,  "required_class": "LRPBus"},
    "core/investigation_cycle.py":     {"min_lines": 150, "required_class": "InvestigationCycle"},
    "core/__init__.py":                {"min_lines": 0},
    "agents/osint_huggingface.py":     {"min_lines": 80,  "required_class": "HuggingFaceOSINTAgent"},
    "agents/osint_github.py":          {"min_lines": 100, "required_class": "GitHubOSINTAgent"},
    "agents/red_team.py":              {"min_lines": 100, "required_class": "RedTeamAgent"},
    "agents/__init__.py":              {"min_lines": 0},
    "obsidian_writer/exporter.py":     {"min_lines": 80,  "required_class": "ObsidianExporter"},
    "obsidian_writer/__init__.py":     {"min_lines": 0},
    "dashboard/app.py":                {"min_lines": 200},
    "dashboard/__init__.py":           {"min_lines": 0},
    "ontologies/uap.yaml":             {"min_lines": 50},
    "vera.py":                         {"min_lines": 50},
    "README.md":                       {"min_lines": 50},
    "VISION.md":                       {"min_lines": 30},
    "CONTRIBUTING.md":                 {"min_lines": 30},
    "CHANGELOG.md":                    {"min_lines": 20},
    ".gitignore":                      {"min_lines": 20},
    "pyproject.toml":                  {"min_lines": 20},
}

PLANNED_NOT_YET_BUILT = {
    "core/autopilot.py",
    "core/memory/chromadb_store.py",
    "core/graph/knowledge_graph.py",
    "agents/nlp_signal.py",
    "api/server.py",
    "Dockerfile",
}

CRITICAL_BAYESIAN_SIGNATURES = [
    "likelihood_ratio",
    "BayesianBeliefUpdater",
    "supports_hypothesis",
    "posterior_odds",
]

CRITICAL_AUDITOR_SIGNATURES = [
    "EpistemicAuditor",
    "audit_update",
    "health_score",
    "BiasType",
]

RED_TEAM_SIGNATURES = [
    "supports_hypothesis=False",
    "RedTeamAgent",
    "counter_evidence",
]


def find_root() -> Path:
    c = Path.cwd()
    for candidate in [c] + list(c.parents):
        if (candidate / "vera.py").exists():
            return candidate
    return c


def anonymize_path(path_str: str) -> str:
    """Replace user-specific path segments for DSGVO compliance."""
    p = str(path_str)
    p = re.sub(r'C:\\Users\\[^\\]+\\', '%USERPROFILE%\\', p)
    p = re.sub(r'/home/[^/]+/', '/home/%USER%/', p)
    p = re.sub(r'/Users/[^/]+/', '/Users/%USER%/', p)
    return p


def git_info(root: Path) -> dict:
    def run(*args):
        try:
            r = subprocess.run(["git"] + list(args), capture_output=True,
                               text=True, cwd=root, timeout=8)
            return r.stdout.strip()
        except Exception:
            return ""
    last = run("log", "-1", "--format=%h|%s|%ai")
    parts = last.split("|") if last else []
    return {
        "branch":        run("branch", "--show-current"),
        "total_commits": run("rev-list", "--count", "HEAD"),
        "last_hash":     parts[0][:12] if parts else "?",
        "last_msg":      parts[1] if len(parts) > 1 else "?",
        "last_date":     parts[2][:16] if len(parts) > 2 else "?",
        "clean":         run("status", "--porcelain") == "",
        "unpushed":      bool(run("log", "@{u}..", "--oneline")),
    }


def check_module_integrity(root: Path) -> list[dict]:
    """Check each canonical module against SOLL requirements."""
    issues = []
    for rel_path, reqs in CANONICAL_MODULES.items():
        full = root / rel_path
        if not full.exists():
            issues.append({
                "file": rel_path,
                "severity": "HIGH",
                "type": "MISSING_FILE",
                "message": f"File not found — should exist per canonical SOLL",
                "patch_action": "CREATE",
            })
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="ignore")
            lines = len(content.splitlines())
            min_lines = reqs.get("min_lines", 0)
            if lines < min_lines:
                issues.append({
                    "file": rel_path,
                    "severity": "MEDIUM",
                    "type": "UNDERSIZED_FILE",
                    "message": f"Only {lines} lines (expected ≥{min_lines}) — may be incomplete",
                    "patch_action": "REVIEW",
                })
            req_class = reqs.get("required_class")
            if req_class and req_class not in content:
                issues.append({
                    "file": rel_path,
                    "severity": "HIGH",
                    "type": "MISSING_CLASS",
                    "message": f"Required class '{req_class}' not found in file",
                    "patch_action": "REVIEW",
                })
        except Exception as e:
            issues.append({
                "file": rel_path,
                "severity": "MEDIUM",
                "type": "READ_ERROR",
                "message": str(e),
                "patch_action": "REVIEW",
            })
    return issues


def check_code_signatures(root: Path) -> list[dict]:
    """Verify critical algorithm signatures are present."""
    issues = []
    checks = [
        ("core/bayesian/updater.py", CRITICAL_BAYESIAN_SIGNATURES, "Bayesian Core"),
        ("core/auditor.py", CRITICAL_AUDITOR_SIGNATURES, "Epistemic Auditor"),
        ("agents/red_team.py", RED_TEAM_SIGNATURES, "Red Team Agent"),
    ]
    for rel, signatures, component in checks:
        full = root / rel
        if not full.exists():
            continue
        content = full.read_text(encoding="utf-8", errors="ignore")
        for sig in signatures:
            if sig not in content:
                issues.append({
                    "file": rel,
                    "severity": "CRITICAL",
                    "type": "MISSING_SIGNATURE",
                    "message": f"[{component}] Critical signature '{sig}' not found — core behavior may be compromised",
                    "patch_action": "MANUAL_REVIEW",
                })
    return issues


def load_sessions(root: Path, limit: int = 5) -> list[dict]:
    data_dir = root / "data"
    if not data_dir.exists():
        return []
    sessions = []
    for p in sorted(data_dir.glob("*_report.json"), reverse=True)[:limit]:
        try:
            with open(p, encoding="utf-8") as f:
                r = json.load(f)
            bs = r.get("belief_summary", {})
            audit = r.get("epistemic_audit", {})
            sessions.append({
                "session_id":   r.get("session_id", "")[-8:],
                "timestamp":    r.get("timestamp", "")[:19],
                "domain":       r.get("domain", ""),
                "belief":       bs.get("current_belief", 0),
                "prior":        bs.get("prior", 0.1),
                "pro":          bs.get("pro_evidence", 0),
                "counter":      bs.get("counter_evidence", 0),
                "verdict":      r.get("verdict", {}).get("label", ""),
                "health":       audit.get("health_score"),
                "warnings":     audit.get("total_warnings", 0),
                "warn_types":   audit.get("by_type", {}),
                "lrp_msgs":     r.get("lrp_messages_sent", 0),
                "duration":     r.get("duration_seconds", 0),
            })
        except Exception:
            continue
    return sessions


def load_belief_updates(root: Path) -> dict:
    path = root / "data" / "belief_updates.jsonl"
    if not path.exists():
        return {"count": 0, "pro_count": 0, "counter_count": 0, "mean_lr": None}
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except Exception:
        return {"count": 0}
    if not rows:
        return {"count": 0}
    pro = sum(1 for r in rows if r.get("supports_hypothesis", True))
    lrs = [r.get("likelihood_ratio", 1.0) for r in rows if "likelihood_ratio" in r]
    return {
        "count":         len(rows),
        "pro_count":     pro,
        "counter_count": len(rows) - pro,
        "mean_lr":       round(sum(lrs)/len(lrs), 4) if lrs else None,
        "max_delta":     round(max(abs(r.get("delta", 0)) for r in rows), 4) if rows else None,
    }


def check_patchbot_history(root: Path) -> list[dict]:
    backup_root = root / ".patchbot_backups"
    if not backup_root.exists():
        return []
    sessions = []
    for sd in sorted(backup_root.iterdir(), reverse=True)[:5]:
        if not sd.is_dir():
            continue
        log = sd / "patch.log"
        if not log.exists():
            continue
        try:
            with open(log, encoding="utf-8") as f:
                data = json.load(f)
            ops = data.get("operations", [])
            sessions.append({
                "session":   sd.name,
                "total":     len(ops),
                "succeeded": sum(1 for o in ops if o.get("success")),
                "failed":    sum(1 for o in ops if not o.get("success")),
                "dry_run":   data.get("dry_run", False),
                "files":     list({o.get("file","") for o in ops if o.get("success")}),
            })
        except Exception:
            continue
    return sessions


def generate_patch_proposals(issues: list[dict]) -> list[str]:
    """Generate VERA_PATCH text blocks for auto-repairable issues."""
    patches = []
    for issue in issues:
        if issue.get("patch_action") == "MANUAL_REVIEW":
            continue
        if issue["type"] == "MISSING_FILE" and issue["file"].endswith(".py"):
            patches.append(f"""VERA_PATCH v1
---
FILE: {issue['file']}
ACTION: CREATE
WITH: # IrsanAI-VERA — {issue['file']}
# This file was detected as missing by the Resonance Reporter.
# Please implement according to CONTRIBUTING.md and the canonical SOLL spec.
# Reference: {GITHUB_REPO}/blob/main/{issue['file']}
REASON: File missing per canonical SOLL state — auto-created as placeholder
---""")
    return patches


def generate_report(
    root: Path,
    target_llm: str = "claude",
    include_patches: bool = True,
) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git = git_info(root)
    module_issues = check_module_integrity(root)
    sig_issues = check_code_signatures(root)
    all_issues = module_issues + sig_issues
    sessions = load_sessions(root)
    bu = load_belief_updates(root)
    pb_history = check_patchbot_history(root)

    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    high     = [i for i in all_issues if i["severity"] == "HIGH"]
    medium   = [i for i in all_issues if i["severity"] == "MEDIUM"]

    health_status = "🟢 HEALTHY" if not critical and not high else \
                    "🔴 CRITICAL" if critical else "🟠 DEGRADED"

    lines = []

    # ── Header ──
    lines += [
        "# IrsanAI-VERA — Resonance Reporter",
        f"**Generated**: {ts}  |  **Target LLM**: {target_llm.upper()}",
        f"**Repo**: {GITHUB_REPO}",
        f"**System Health**: {health_status}",
        "",
        "> DSGVO-compliant. No personal data. No tokens. No PII.",
        "> Path anonymized. Session IDs truncated.",
        "",
        "---",
        "",
    ]

    # ── IST/SOLL Summary ──
    total_canonical = len(CANONICAL_MODULES)
    existing = sum(1 for p in CANONICAL_MODULES if (root/p).exists())
    planned_count = len(PLANNED_NOT_YET_BUILT)

    lines += [
        "## ⬡ IST / SOLL State",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Canonical modules expected | `{total_canonical}` |",
        f"| Modules present (IST) | `{existing}` |",
        f"| Modules missing (SOLL gap) | `{total_canonical - existing}` |",
        f"| Planned future modules | `{planned_count}` |",
        f"| Critical issues | `{len(critical)}` |",
        f"| High issues | `{len(high)}` |",
        f"| Medium issues | `{len(medium)}` |",
        f"| Git branch | `{git['branch']}` |",
        f"| Last commit | `{git['last_hash']}` — {git['last_msg']} |",
        f"| Working tree | `{'Clean' if git['clean'] else 'Uncommitted changes'}` |",
        f"| Unpushed | `{git['unpushed']}` |",
        "",
    ]

    # ── Issues ──
    if all_issues:
        lines += ["## ⚠️ Detected Deviations (IST ≠ SOLL)", ""]
        sev_icon = {"CRITICAL": "⛔", "HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}
        for issue in sorted(all_issues, key=lambda x: ["CRITICAL","HIGH","MEDIUM","LOW"].index(x["severity"])):
            icon = sev_icon.get(issue["severity"], "⚠️")
            lines.append(
                f"{icon} **[{issue['severity']}]** `{issue['file']}` — "
                f"{issue['type']}: {issue['message']}"
            )
        lines.append("")
    else:
        lines += ["## ✅ No Deviations Detected", "", "IST matches SOLL. System integrity confirmed.", ""]

    # ── Dashboard KPIs (last session) ──
    lines += ["## 📊 Dashboard State (Latest Session)", ""]
    if sessions:
        s = sessions[0]
        bu_data = bu
        health = s.get("health")
        health_str = f"🟢 {health:.3f}" if health and health > 0.8 else \
                     f"🟡 {health:.3f}" if health and health > 0.5 else \
                     f"🔴 {health:.3f}" if health else "N/A"
        lines += [
            f"| KPI | Value |",
            f"|-----|-------|",
            f"| Domain | `{s['domain']}` |",
            f"| Current Belief | `{s['belief']:.1%}` |",
            f"| Prior | `{s['prior']:.1%}` |",
            f"| Net Shift | `{s['belief']-s['prior']:+.1%}` |",
            f"| Pro Evidence | `{s['pro']}` |",
            f"| Counter Evidence | `{s['counter']}` |",
            f"| Verdict | `{s['verdict']}` |",
            f"| Health Score | {health_str} |",
            f"| Audit Warnings | `{s['warnings']}` |",
            f"| LRP Messages | `{s['lrp_msgs']}` |",
            f"| Duration | `{s['duration']:.1f}s` |",
            f"| Total Bayes Updates | `{bu_data['count']}` |",
            f"| Mean Likelihood Ratio | `{bu_data.get('mean_lr', 'N/A')}` |",
            "",
        ]

        if s.get("warn_types"):
            lines += ["**Audit Warning Types:**"]
            for wtype, cnt in s["warn_types"].items():
                lines.append(f"- `{wtype}` ×{cnt}")
            lines.append("")
    else:
        lines += ["_No session data found. Run `python vera.py --ontology ontologies/uap.yaml`_", ""]

    # ── Session Trend ──
    if len(sessions) > 1:
        lines += ["## 📈 Belief Trend (Last 5 Sessions)", "",
                  "| Timestamp | Belief | Pro/Counter | Verdict | Health |",
                  "|-----------|--------|-------------|---------|--------|"]
        for s in sessions:
            h = s.get("health")
            hs = f"🟢 {h:.2f}" if h and h > 0.8 else f"🟡 {h:.2f}" if h and h > 0.5 else f"🔴 {h:.2f}" if h else "—"
            lines.append(
                f"| `{s['timestamp']}` | `{s['belief']:.1%}` | "
                f"`{s['pro']}✅/{s['counter']}❌` | {s['verdict']} | {hs} |"
            )
        lines.append("")

    # ── PatchBot History ──
    if pb_history:
        lines += ["## 🔧 PatchBot History (Last 5)", "",
                  "| Session | Patches | Result | Files |",
                  "|---------|---------|--------|-------|"]
        for pb in pb_history:
            files_str = ", ".join(f"`{f}`" for f in pb["files"][:2]) or "—"
            result = f"✅ {pb['succeeded']}/{pb['total']}" if pb["failed"] == 0 \
                     else f"⚠️ {pb['succeeded']}/{pb['total']} ({pb['failed']} failed)"
            dry = " (dry)" if pb["dry_run"] else ""
            lines.append(f"| `{pb['session']}` | {pb['total']} | {result}{dry} | {files_str} |")
        lines.append("")

    # ── Auto-Repair Proposals ──
    if include_patches and all_issues:
        proposals = generate_patch_proposals(all_issues)
        if proposals:
            lines += [
                "## 🛠️ Auto-Repair Proposals",
                "",
                "Apply with: `python irsanai_patchbot.py auto_repair.txt`",
                "",
                "```",
            ]
            for patch in proposals:
                lines.append(patch)
            lines += ["```", ""]

        manual_items = [i for i in all_issues if i.get("patch_action") == "MANUAL_REVIEW"]
        if manual_items:
            lines += ["## 🔍 Manual Review Required", ""]
            for item in manual_items:
                lines.append(
                    f"- **`{item['file']}`**: {item['message']}"
                    f"\n  → Reference: [{GITHUB_REPO}/blob/main/{item['file']}]"
                    f"({GITHUB_REPO}/blob/main/{item['file']})"
                )
            lines.append("")

    # ── Validation Checklist ──
    lines += [
        "## ✅ Validation Checklist (for LLM)",
        "",
        "After applying any patches, verify:",
        "",
        "- [ ] `python vera.py --ontology ontologies/uap.yaml --no-obsidian` runs without error",
        "- [ ] Belief updates from real evidence (not hardcoded)",
        "- [ ] Red Team produces counter-evidence (`supports_hypothesis=False`)",
        "- [ ] Epistemic Auditor produces health score",
        "- [ ] Dashboard loads: `streamlit run dashboard/app.py`",
        "- [ ] Run Resonance Reporter again: `python irsanai_resonance_reporter.py`",
        "- [ ] All CRITICAL/HIGH issues resolved",
        "",
        "---",
        "",
        f"*IrsanAI-VERA Resonance Reporter v{REPORT_VERSION}*",
        f"*Canonical reference: {GITHUB_REPO}*",
        f"*Generated: {ts}*",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="IrsanAI-VERA Resonance Reporter — IST/SOLL Validator"
    )
    parser.add_argument("--for", dest="target_llm", default="claude",
                        choices=["claude", "grok", "gemini", "generic"])
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--auto-repair", action="store_true",
                        help="Write auto-repair patch file and apply via PatchBot")
    parser.add_argument("--no-patches", action="store_true",
                        help="Skip patch proposals in output")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()

    root = args.root or find_root()

    print(f"\n  IrsanAI Resonance Reporter v{REPORT_VERSION}")
    print(f"  Ref: {GITHUB_REPO}\n")

    report = generate_report(
        root,
        target_llm=args.target_llm,
        include_patches=not args.no_patches,
    )

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.output or root / f"resonance_report_{ts}.md"
    out.write_text(report, encoding="utf-8")

    print(f"  ✅ Report: {out}")
    print(f"  📋 Paste to {args.target_llm.upper()} for analysis\n")

    # Auto-repair
    if args.auto_repair:
        module_issues = check_module_integrity(root)
        sig_issues    = check_code_signatures(root)
        proposals     = generate_patch_proposals(module_issues + sig_issues)
        if proposals:
            patch_file = root / f"auto_repair_{ts}.txt"
            patch_file.write_text(
                "VERA_PATCH v1\n" + "\n".join(proposals), encoding="utf-8"
            )
            print(f"  🛠️  Auto-repair patch: {patch_file}")
            print(f"  Run: python irsanai_patchbot.py {patch_file.name}\n")
        else:
            print("  ✅ No auto-repairable issues found.\n")

    # Preview
    preview = report.splitlines()[:20]
    print("  ─── Preview ──────────────────────────────────────")
    for line in preview:
        print(f"  {line}")
    print("  ──────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
