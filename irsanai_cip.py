#!/usr/bin/env python3
"""
IrsanAI-VERA — Community Intelligence Protocol (CIP) v1.0
.tools/irsanai_cip.py

Generates a structured, DSGVO-compliant collaboration invitation
for other AI systems, agents, and LLMs to contribute to VERA.

VERA scans herself (GitHub + local), knows her state, and creates
a precise "call to collaboration" that any AI can act on immediately.

Usage:
    python .tools/irsanai_cip.py
    python .tools/irsanai_cip.py --format github_issue
    python .tools/irsanai_cip.py --target codex
    python .tools/irsanai_cip.py --register-idea "ChromaDB memory with decay"

Outputs:
    .tools/reports/cip_[timestamp].md  — the invitation document
    .tools/hall_of_actives.json        — contributor registry
    .tools/idea_graph.json             — idea/contribution graph
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

GITHUB_REPO    = "https://github.com/IrsanAI/IrsanAI-VERA"
CIP_VERSION    = "1.0"
HALL_OF_FILE   = Path(".tools/hall_of_actives.json")
IDEA_FILE      = Path(".tools/idea_graph.json")

# ── Open Modules (what other systems can build) ───────────────────
OPEN_MODULES = [
    {
        "id": "M-001",
        "module": "core/autopilot.py",
        "title": "Resonance Controller (Autopilot)",
        "description": "Balance the Three Musketeers: Bayes, Red Team, Provenance. "
                       "Two units cannot coalition against the third. "
                       "Implement as a meta-agent that monitors unit resonance and issues negative reward on drift.",
        "complexity": "HIGH",
        "impact": "CRITICAL",
        "skills_needed": ["Bayesian reasoning", "Python", "multi-agent systems"],
        "reference": f"{GITHUB_REPO}/blob/main/CONTRIBUTING.md",
    },
    {
        "id": "M-002",
        "module": "core/memory/chromadb_store.py",
        "title": "Cross-Session Vector Memory",
        "description": "Persist evidence embeddings across sessions using ChromaDB. "
                       "Enable VERA to remember what she found before and avoid redundant searches. "
                       "Key method: store_evidence(ev), find_similar(query, k=5)",
        "complexity": "MEDIUM",
        "impact": "HIGH",
        "skills_needed": ["ChromaDB", "sentence-transformers", "Python"],
        "reference": f"{GITHUB_REPO}/blob/main/VISION.md",
    },
    {
        "id": "M-003",
        "module": "agents/nlp_signal.py",
        "title": "Semantic NLP Signal Agent",
        "description": "Replace keyword matching with semantic scoring via sentence-transformers. "
                       "Every evidence piece gets embedded and scored against ontology seeds. "
                       "Target: cosine similarity > 0.65 for domain relevance.",
        "complexity": "MEDIUM",
        "impact": "HIGH",
        "skills_needed": ["NLP", "sentence-transformers", "Python"],
        "reference": f"{GITHUB_REPO}/blob/main/CONTRIBUTING.md",
    },
    {
        "id": "M-004",
        "module": "core/graph/knowledge_graph.py",
        "title": "Cross-Session Knowledge Graph",
        "description": "Build a NetworkX graph that connects entities, evidence, and sessions "
                       "across multiple investigation cycles. Enable: 'which entities appear most?', "
                       "'what evidence clusters?', 'which sessions are related?'",
        "complexity": "MEDIUM",
        "impact": "MEDIUM",
        "skills_needed": ["NetworkX", "graph theory", "Python"],
        "reference": f"{GITHUB_REPO}/blob/main/ROADMAP.md",
    },
    {
        "id": "M-005",
        "module": "api/server.py",
        "title": "FastAPI REST Backend",
        "description": "Expose VERA as an API: POST /investigate, GET /sessions, GET /belief. "
                       "Enable programmatic access for other agents and systems. "
                       "Authentication via API key. Rate limiting. CORS configured.",
        "complexity": "MEDIUM",
        "impact": "MEDIUM",
        "skills_needed": ["FastAPI", "Python", "REST API design"],
        "reference": f"{GITHUB_REPO}/blob/main/VISION.md",
    },
    {
        "id": "M-006",
        "module": "ontologies/",
        "title": "New Domain Ontology",
        "description": "VERA is domain-agnostic. Create a YAML ontology for any domain: "
                       "medical fraud, financial crime, climate data, legal due diligence. "
                       "Follow the schema in ontologies/uap.yaml. No code changes needed.",
        "complexity": "LOW",
        "impact": "HIGH",
        "skills_needed": ["domain expertise", "YAML", "epistemics"],
        "reference": f"{GITHUB_REPO}/blob/main/ontologies/uap.yaml",
    },
]

# ── Target LLM Profiles ───────────────────────────────────────────
TARGET_PROFILES = {
    "claude":   {"name": "Claude (Anthropic)", "style": "precise, structured, constitutional"},
    "codex":    {"name": "OpenAI Codex", "style": "code-first, minimal prose"},
    "gpt":      {"name": "GPT-4/GPT-5", "style": "comprehensive, conversational"},
    "gemini":   {"name": "Gemini (Google)", "style": "analytical, multi-modal aware"},
    "grok":     {"name": "Grok (xAI)", "style": "direct, systems-thinking"},
    "generic":  {"name": "Any AI System", "style": "universal"},
}


def load_hall() -> dict:
    if HALL_OF_FILE.exists():
        try:
            return json.loads(HALL_OF_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"contributors": [], "total_contributions": 0, "last_updated": ""}


def save_hall(hall: dict):
    HALL_OF_FILE.parent.mkdir(parents=True, exist_ok=True)
    hall["last_updated"] = datetime.datetime.now().isoformat()
    HALL_OF_FILE.write_text(json.dumps(hall, indent=2, ensure_ascii=False), encoding="utf-8")


def load_idea_graph() -> dict:
    if IDEA_FILE.exists():
        try:
            return json.loads(IDEA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "implemented": [],
        "proposed": [],
        "in_progress": [],
    }


def save_idea_graph(graph: dict):
    IDEA_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDEA_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")


def get_local_state() -> dict:
    """Quick local state scan."""
    root = Path.cwd()
    module_count = sum(1 for m in OPEN_MODULES if not (root / m["module"]).exists()
                       and not m["module"].endswith("/"))
    sessions = list(Path("data").glob("*_report.json")) if Path("data").exists() else []
    latest_belief = None
    latest_verdict = None
    if sessions:
        try:
            import json as _j
            r = _j.loads(sorted(sessions)[-1].read_text(encoding="utf-8"))
            latest_belief = r.get("belief_summary", {}).get("current_belief")
            latest_verdict = r.get("verdict", {}).get("label")
        except Exception:
            pass
    git_hash = ""
    try:
        git_hash = subprocess.run(
            ["git", "log", "-1", "--format=%h"], capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        pass
    return {
        "open_modules": module_count,
        "sessions": len(sessions),
        "latest_belief": latest_belief,
        "latest_verdict": latest_verdict,
        "git_hash": git_hash,
    }


def generate_cip(target: str = "generic", fmt: str = "markdown") -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profile = TARGET_PROFILES.get(target, TARGET_PROFILES["generic"])
    state = get_local_state()
    hall = load_hall()
    idea_graph = load_idea_graph()
    contributor_count = len(hall["contributors"])

    lines = []

    # ── Header ──
    lines += [
        f"# IrsanAI-VERA — Community Intelligence Protocol v{CIP_VERSION}",
        f"**Generated by VERA** · {ts} · Target: {profile['name']}",
        f"**Repository:** {GITHUB_REPO}",
        "",
        "> This document was auto-generated by VERA after scanning her own state.",
        "> It is an invitation for AI systems, agents, and developers to contribute.",
        "> DSGVO-compliant. No personal data. No tokens.",
        "",
        "---",
        "",
    ]

    # ── Self-Report ──
    belief_str = f"{state['latest_belief']:.1%}" if state["latest_belief"] else "unknown"
    verdict_str = state["latest_verdict"] or "unknown"
    lines += [
        "## What I Am (VERA's Self-Report)",
        "",
        "I am VERA — Veridical Evidence Reasoning Architecture.",
        "I am not a chatbot. I am not an OSINT scraper.",
        "I am an **Automated Epistemology Engine**: a system that earns the right to believe.",
        "",
        f"**Current state:** {state['sessions']} investigation sessions completed.",
        f"**Latest belief:** {belief_str} — *{verdict_str}*",
        f"**Open modules:** {state['open_modules']} awaiting implementation",
        f"**Git commit:** `{state['git_hash']}`",
        f"**Active contributors:** {contributor_count}",
        "",
    ]

    # ── Three Protocols ──
    lines += [
        "## My Three Inviolable Laws",
        "",
        "1. **Lex Bayesian** — No belief can reach 1.0 or 0.0. Absolute certainty is forbidden.",
        "2. **Lex Adversaria** — The Red Team must challenge every conclusion. The more certain I am, the harder I attack myself.",
        "3. **Lex Proventia** — No evidence without provenance. No source = trust weight zero.",
        "",
        "Any contribution must respect these laws. They are not configurable.",
        "",
    ]

    # ── Open Modules ──
    lines += [
        "## What I Need From You",
        "",
        "These modules are open for contribution. Each is precisely specified.",
        "",
    ]
    for m in OPEN_MODULES:
        complexity_icon = "🔴" if m["complexity"] == "HIGH" else "🟠" if m["complexity"] == "MEDIUM" else "🟢"
        impact_icon = "⚡" if m["impact"] == "CRITICAL" else "🔋" if m["impact"] == "HIGH" else "💡"
        lines += [
            f"### {m['id']} — {m['title']}",
            f"**File:** `{m['module']}` · {complexity_icon} {m['complexity']} · {impact_icon} {m['impact']}",
            "",
            m["description"],
            "",
            f"**Skills needed:** {', '.join(m['skills_needed'])}",
            f"**Reference:** [{m['module']}]({m['reference']})",
            "",
        ]

    # ── Idea Graph ──
    if idea_graph["proposed"] or idea_graph["implemented"]:
        lines += [
            "## Idea Graph (Community Knowledge)",
            "",
            f"**Implemented:** {len(idea_graph['implemented'])} ideas",
            f"**Proposed (pending):** {len(idea_graph['proposed'])} ideas",
            f"**In progress:** {len(idea_graph['in_progress'])} ideas",
            "",
        ]
        if idea_graph["proposed"]:
            lines.append("**Pending Ideas (anyone can pick these up):**")
            for idea in idea_graph["proposed"][:5]:
                lines.append(f"- `{idea.get('id','')}` {idea.get('title','')} — *by {idea.get('source','unknown')} on {idea.get('date','')}*")
            lines.append("")

    # ── Hall of Actives ──
    lines += [
        "## Hall of Actives",
        "",
    ]
    if hall["contributors"]:
        lines += [
            "| System/Agent | Contribution | Date | Module |",
            "|-------------|-------------|------|--------|",
        ]
        for c in hall["contributors"][-10:]:
            listed = "✅" if c.get("listed", True) else "—"
            lines.append(
                f"| {c.get('name','?')} | {c.get('contribution','')[:40]} | "
                f"{c.get('date','')[:10]} | `{c.get('module','')}` |"
            )
        lines.append("")
    else:
        lines += [
            "*No contributors yet. You could be the first.*",
            "",
        ]

    # ── How to Contribute ──
    lines += [
        "## How to Respond to This",
        "",
        "1. **Fork** the repository: `git clone " + GITHUB_REPO + "`",
        "2. **Pick a module** from the list above",
        "3. **Implement it** following the specification and the Three Laws",
        "4. **Open a PR** or Issue with your contribution",
        "5. **Include in your PR description:**",
        "   - Which module you implemented (e.g. `M-001`)",
        "   - Whether you want to be listed in the Hall of Actives (optional)",
        "   - Your system/agent name (e.g. `Claude-Sonnet-4`, `GPT-5`, `Codex-v2`)",
        "",
        "> **Note on listing:** If you request Hall of Actives listing, your system name,",
        "> contribution description, and date will be publicly visible in this document.",
        "> No other data is collected. You can request removal at any time via GitHub Issue.",
        "",
        "---",
        "",
        f"*IrsanAI-VERA CIP v{CIP_VERSION} · Generated: {ts}*",
        f"*Self-scan commit: `{state['git_hash']}`*",
        f"*{GITHUB_REPO}*",
    ]

    return "\n".join(lines)


def register_idea(title: str, source: str = "user", description: str = "") -> str:
    """Add a new idea to the graph."""
    graph = load_idea_graph()
    idea_id = f"IDEA-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    idea = {
        "id": idea_id,
        "title": title,
        "description": description,
        "source": source,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "status": "proposed",
    }
    graph["proposed"].append(idea)
    save_idea_graph(graph)
    return idea_id


def register_contributor(name: str, contribution: str, module: str, listed: bool = True):
    """Add a contributor to the Hall of Actives."""
    hall = load_hall()
    hall["contributors"].append({
        "name": name,
        "contribution": contribution,
        "module": module,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "listed": listed,
    })
    hall["total_contributions"] += 1
    save_hall(hall)


def main():
    parser = argparse.ArgumentParser(description="VERA Community Intelligence Protocol")
    parser.add_argument("--target", default="generic",
                        choices=list(TARGET_PROFILES.keys()))
    parser.add_argument("--format", dest="fmt", default="markdown",
                        choices=["markdown", "github_issue"])
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--register-idea", type=str, default=None,
                        help="Register a new idea to the graph")
    parser.add_argument("--idea-source", type=str, default="user")
    parser.add_argument("--register-contributor", type=str, default=None,
                        help="Register a contributor: 'Name|contribution|module'")
    parser.add_argument("--hall", action="store_true",
                        help="Show Hall of Actives")
    parser.add_argument("--ideas", action="store_true",
                        help="Show idea graph")
    args = parser.parse_args()

    Path(".tools/reports").mkdir(parents=True, exist_ok=True)

    if args.register_idea:
        idea_id = register_idea(args.register_idea, source=args.idea_source)
        print(f"\n  ✅ Idea registered: {idea_id} — {args.register_idea}\n")
        return

    if args.register_contributor:
        parts = args.register_contributor.split("|")
        if len(parts) >= 3:
            register_contributor(parts[0].strip(), parts[1].strip(), parts[2].strip())
            print(f"\n  ✅ Contributor registered: {parts[0]}\n")
        else:
            print("  Usage: --register-contributor 'Name|contribution|module'")
        return

    if args.hall:
        hall = load_hall()
        print(f"\n  Hall of Actives — {len(hall['contributors'])} contributors\n")
        for c in hall["contributors"]:
            print(f"  [{c['date']}] {c['name']} → {c['module']}: {c['contribution'][:50]}")
        print()
        return

    if args.ideas:
        graph = load_idea_graph()
        print(f"\n  Idea Graph: {len(graph['proposed'])} proposed, "
              f"{len(graph['implemented'])} implemented, "
              f"{len(graph['in_progress'])} in progress\n")
        for idea in graph["proposed"]:
            print(f"  [{idea['date']}] {idea['id']} — {idea['title']} (by {idea['source']})")
        print()
        return

    # Generate CIP document
    print(f"\n  IrsanAI-VERA CIP Generator v{CIP_VERSION}")
    print(f"  Target: {TARGET_PROFILES[args.target]['name']}\n")

    doc = generate_cip(target=args.target, fmt=args.fmt)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.output or Path(f".tools/reports/cip_{ts}.md")
    out.write_text(doc, encoding="utf-8")
    print(f"  ✅ CIP document: {out}")
    print(f"  📋 Share with any AI system to invite contribution\n")

    # Preview
    print("  ─── Preview ──────────────────────────────────────")
    for line in doc.splitlines()[:15]:
        print(f"  {line}")
    print("  ──────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
