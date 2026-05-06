#!/usr/bin/env python3
"""
IrsanAI PatchBot — Status Reporter Extension
irsanai_patchbot_status.py

On-Demand Snapshot Generator für Online-LLMs.
Generiert einen kompakten, DSGVO-konformen Report über den aktuellen
lokalen Projektzustand — optimiert für direktes Copy-Paste zu Claude,
Grok, Gemini oder anderen Online-LLMs.

Usage:
    python irsanai_patchbot_status.py
    python irsanai_patchbot_status.py --for claude
    python irsanai_patchbot_status.py --full
    python irsanai_patchbot_status.py --actions-only
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path


def find_root() -> Path:
    current = Path.cwd()
    for c in [current] + list(current.parents):
        if (c / "vera.py").exists():
            return c
    return current


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
    recent = run("log", "-3", "--format=%h %s").splitlines()

    return {
        "branch": run("branch", "--show-current"),
        "remote": run("remote", "get-url", "origin"),
        "commits": run("rev-list", "--count", "HEAD"),
        "last_hash": parts[0] if parts else "?",
        "last_msg": parts[1] if len(parts) > 1 else "?",
        "last_date": parts[2][:16] if len(parts) > 2 else "?",
        "recent": recent,
        "clean": run("status", "--porcelain") == "",
        "unpushed": run("log", "@{u}..", "--oneline"),
    }


def patchbot_actions(root: Path, limit: int = 5) -> list[dict]:
    """Read last N PatchBot sessions from .patchbot_backups/"""
    backup_root = root / ".patchbot_backups"
    if not backup_root.exists():
        return []

    sessions = sorted(backup_root.iterdir(), reverse=True)
    actions = []

    for session_dir in sessions[:limit]:
        if not session_dir.is_dir():
            continue
        log_path = session_dir / "patch.log"
        if not log_path.exists():
            continue
        try:
            with open(log_path, encoding="utf-8") as f:
                log = json.load(f)

            ops = log.get("operations", [])
            ok = sum(1 for o in ops if o["success"])
            failed_ops = [o for o in ops if not o["success"]]

            # Generate unique action key (session_id + hash of operations)
            action_key = f"PB-{session_dir.name}"

            actions.append({
                "session_id": session_dir.name,
                "action_key": action_key,
                "timestamp": ops[0]["timestamp"][:19] if ops else session_dir.name,
                "total": len(ops),
                "succeeded": ok,
                "failed": len(failed_ops),
                "dry_run": log.get("dry_run", False),
                "files_touched": list({o["file"] for o in ops if o["success"] and not log.get("dry_run")}),
                "errors": [{"file": o["file"], "msg": o["message"]} for o in failed_ops],
                "status": "✅ Clean" if len(failed_ops) == 0 else f"⚠️ {len(failed_ops)} error(s)",
            })
        except Exception:
            continue

    return actions


def vera_sessions(root: Path, limit: int = 3) -> list[dict]:
    """Read last N VERA session reports."""
    data_dir = root / "data"
    if not data_dir.exists():
        return []

    reports = sorted(data_dir.glob("*_report.json"), reverse=True)[:limit]
    sessions = []

    for rp in reports:
        try:
            with open(rp, encoding="utf-8") as f:
                r = json.load(f)
            bs = r.get("belief_summary", {})
            audit = r.get("epistemic_audit", {})
            sessions.append({
                "session_id": r.get("session_id", ""),
                "timestamp": r.get("timestamp", "")[:19],
                "belief": f"{bs.get('current_belief', 0):.1%}",
                "prior": f"{bs.get('prior', 0):.1%}",
                "pro": bs.get("pro_evidence", 0),
                "counter": bs.get("counter_evidence", 0),
                "verdict": r.get("verdict", {}).get("label", ""),
                "health": audit.get("health_score"),
                "warnings": audit.get("total_warnings", 0),
            })
        except Exception:
            continue

    return sessions


def file_map(root: Path) -> dict:
    """Compact file inventory — name + line count per folder."""
    folders = {}
    ignore = {".git", "__pycache__", ".venv", "venv", ".patchbot_backups",
              "node_modules", ".idea"}

    for path in root.rglob("*.py"):
        if any(p in path.parts for p in ignore):
            continue
        folder = str(path.parent.relative_to(root)) or "root"
        if folder not in folders:
            folders[folder] = []
        try:
            lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            lines = 0
        folders[folder].append(f"{path.name} ({lines}L)")

    return folders


def installed_packages(names: list[str]) -> dict:
    import importlib.metadata as meta
    result = {}
    for pkg in names:
        try:
            result[pkg] = meta.version(pkg)
        except meta.PackageNotFoundError:
            result[pkg] = "MISSING"
    return result


def generate_report(root: Path, mode: str = "standard", target_llm: str = "claude") -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git = git_info(root)
    pb_actions = patchbot_actions(root, limit=5)
    vera = vera_sessions(root, limit=3)
    files = file_map(root)

    key_packages = ["requests", "pyyaml", "streamlit", "networkx",
                    "chromadb", "sentence_transformers", "torch", "psutil"]
    pkgs = installed_packages(key_packages)

    lines = []

    # ── Header ──
    lines += [
        f"# IrsanAI-VERA — LLM Context Snapshot",
        f"**Generated**: {ts}  |  **Target**: {target_llm.upper()}  |  **Mode**: {mode}",
        f"**Root**: `{root}`",
        "",
        "> DSGVO-konform — kein PII, keine Tokens, keine .env Inhalte.",
        "",
        "---",
        "",
    ]

    # ── Intent Summary (always included) ──
    lines += [
        "## 🎯 Project Intent (for LLM context)",
        "",
        "**IrsanAI-VERA** (Veridical Evidence Reasoning Architecture) ist eine",
        "domain-agnostische, epistemisch ehrliche Multi-Agenten-Engine.",
        "Sie sammelt Evidenz aus echten Quellen (GitHub API, HuggingFace API),",
        "wendet Bayesian Belief Updates an, lässt einen Red Team Agent aktiv",
        "Counter-Evidence suchen, überwacht den eigenen Denkprozess mit einem",
        "Epistemic Auditor (7 Bias-Detektoren), und exportiert alles in einen",
        "Obsidian Knowledge Graph.",
        "",
        "**UAP Disclosure** ist der Proof-of-Concept Domain.",
        "Die Architektur ist domain-agnostisch via YAML Ontologie.",
        "",
        "**GitHub**: https://github.com/IrsanAI/IrsanAI-VERA",
        "",
    ]

    # ── Git State ──
    unpushed_note = f"⚠️ {len(git['unpushed'].splitlines())} unpushed" if git['unpushed'] else "✅ all pushed"
    lines += [
        "## 🔀 Git State",
        "",
        f"| | |",
        f"|---|---|",
        f"| Branch | `{git['branch']}` |",
        f"| Commits | `{git['commits']}` |",
        f"| Last | `{git['last_hash']}` — {git['last_msg']} ({git['last_date']}) |",
        f"| Tree | {'✅ Clean' if git['clean'] else '⚠️ Uncommitted changes'} |",
        f"| Push | {unpushed_note} |",
        "",
        "**Recent commits**:",
    ]
    for c in git['recent']:
        lines.append(f"- `{c}`")
    lines.append("")

    # ── PatchBot Actions ──
    lines += [
        "## 🔧 PatchBot — Last Actions",
        "",
    ]
    if not pb_actions:
        lines.append("_No PatchBot sessions found._")
    else:
        lines += [
            "| Action Key | Timestamp | Files | Result |",
            "|-----------|-----------|-------|--------|",
        ]
        for a in pb_actions:
            files_str = ", ".join(f"`{f}`" for f in a["files_touched"][:3]) or "—"
            dry = " (dry)" if a["dry_run"] else ""
            lines.append(
                f"| `{a['action_key']}` | {a['timestamp']} | "
                f"{files_str} | {a['status']}{dry} |"
            )
        lines.append("")

        # Errors if any
        for a in pb_actions:
            if a["errors"]:
                lines.append(f"**Errors in `{a['action_key']}`**:")
                for e in a["errors"]:
                    lines.append(f"- `{e['file']}`: {e['msg']}")
        lines.append("")

    # ── VERA Sessions ──
    lines += [
        "## 📊 VERA — Last Sessions",
        "",
    ]
    if not vera:
        lines.append("_No VERA sessions found. Run `python vera.py --ontology ontologies/uap.yaml`_")
    else:
        lines += [
            "| Timestamp | Belief | Evidence | Verdict | Health |",
            "|-----------|--------|----------|---------|--------|",
        ]
        for s in vera:
            health = f"🟢 {s['health']:.3f}" if s['health'] and s['health'] > 0.8 else (
                f"🟡 {s['health']:.3f}" if s['health'] else "N/A")
            lines.append(
                f"| {s['timestamp']} | `{s['belief']}` | "
                f"{s['pro']}✅/{s['counter']}❌ | {s['verdict']} | {health} |"
            )
    lines.append("")

    if mode in ("standard", "full"):
        # ── File Map ──
        lines += [
            "## 📁 Python File Map",
            "",
        ]
        for folder, file_list in sorted(files.items()):
            lines.append(f"**`{folder}/`** ({len(file_list)} files)")
            for f in file_list:
                lines.append(f"  - `{f}`")
        lines.append("")

        # ── Packages ──
        lines += ["## 📦 Key Packages", ""]
        ok = [f"`{k}` {v}" for k, v in pkgs.items() if v != "MISSING"]
        missing = [f"`{k}`" for k, v in pkgs.items() if v == "MISSING"]
        if ok:
            lines.append("**Installed**: " + " · ".join(ok))
        if missing:
            lines.append(f"**Missing**: {', '.join(missing)}")
        lines.append("")

    # ── Action Keys Legend ──
    lines += [
        "## 🔑 PatchBot Action Keys",
        "",
        "Diese Keys kannst du verwenden um dem Online-LLM zu sagen",
        "welche Aktion referenziert wird:",
        "",
    ]
    for a in pb_actions[:5]:
        summary = f"{a['succeeded']}/{a['total']} patches OK, files: {', '.join(a['files_touched'][:2]) or 'none'}"
        lines.append(f"- **`{a['action_key']}`** — {a['timestamp']} — {summary}")
    lines.append("")

    # ── Quick Instruction Block for LLM ──
    lines += [
        "---",
        "",
        "## 💬 Für das Online-LLM",
        "",
        "Du bist jetzt vollständig kontextualisiert. Der lokale IrsanAI PatchBot",
        "wartet auf deine Anweisungen im Format:",
        "",
        "```",
        "VERA_PATCH v1",
        "---",
        "FILE: pfad/zur/datei.py",
        "ACTION: REPLACE_LINE",
        "LINE_CONTAINS: \"text der geändert wird\"",
        "WITH: neuer text",
        "REASON: Warum",
        "---",
        "```",
        "",
        f"*IrsanAI PatchBot Status v1.0 — {ts}*",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="IrsanAI PatchBot Status — LLM Context Snapshot"
    )
    parser.add_argument("--for", dest="target_llm", default="claude",
                        choices=["claude", "grok", "gemini", "generic"],
                        help="Target LLM (default: claude)")
    parser.add_argument("--full", action="store_true",
                        help="Include full file map and package list")
    parser.add_argument("--actions-only", action="store_true",
                        help="Only show PatchBot actions")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: auto-named)")
    parser.add_argument("--root", type=Path, default=None)

    args = parser.parse_args()
    root = args.root or find_root()

    mode = "full" if args.full else ("actions" if args.actions_only else "standard")

    print(f"\n  IrsanAI PatchBot Status v1.0")
    print(f"  Generating {mode} snapshot for {args.target_llm.upper()}...\n")

    report = generate_report(root, mode=mode, target_llm=args.target_llm)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.output or root / f"patchbot_status_{ts}.md"
    out.write_text(report, encoding="utf-8")

    print(f"  ✅ Status report saved: {out}")
    print(f"  📋 Copy contents to your Online-LLM\n")

    # Print preview
    preview = report.splitlines()[:25]
    print("  ─── Preview ──────────────────────────────────────────")
    for line in preview:
        print(f"  {line}")
    print("  ─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()