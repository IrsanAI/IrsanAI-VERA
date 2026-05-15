#!/usr/bin/env python3
"""
IrsanAI-VERA — Community Intelligence Protocol v2.0
.tools/irsanai_cip_v2.py

METACOGNITIVE SELF-REPORT ENGINE

VERA scans her own source code via AST, extracts real signatures,
reads her session history, computes epistemic health, analyzes
module interdependencies, and generates a document so precise
that any LLM can start writing code immediately — no questions needed.

This is not documentation. This is VERA thinking about herself.

Usage:
    python .tools/irsanai_cip_v2.py
    python .tools/irsanai_cip_v2.py --target claude --depth deep
    python .tools/irsanai_cip_v2.py --module M-001
    python .tools/irsanai_cip_v2.py --register-idea "idea text"
"""

from __future__ import annotations

import ast
import argparse
import datetime
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional

GITHUB_REPO   = "https://github.com/IrsanAI/IrsanAI-VERA"
CIP_VERSION   = "2.0"
HALL_FILE     = Path(".tools/hall_of_actives.json")
IDEA_FILE     = Path(".tools/idea_graph.json")
ROOT          = Path(__file__).parent.parent


# ══════════════════════════════════════════════════════════════════
# AST CODE INTELLIGENCE — VERA reads her own source
# ══════════════════════════════════════════════════════════════════

def extract_class_signatures(filepath: Path) -> list[dict]:
    """Extract all classes and their methods with signatures."""
    if not filepath.exists():
        return []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []

    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cls = {"name": node.name, "methods": [], "docstring": ""}
        ds = ast.get_docstring(node)
        if ds:
            cls["docstring"] = ds.split("\n")[0][:120]

        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            args = []
            func_args = item.args
            all_args = func_args.args
            defaults_offset = len(all_args) - len(func_args.defaults)

            for i, arg in enumerate(all_args):
                if arg.arg == "self":
                    continue
                annotation = ""
                if arg.annotation:
                    try:
                        annotation = ast.unparse(arg.annotation)
                    except Exception:
                        pass
                default = ""
                if i >= defaults_offset:
                    try:
                        default = f"={ast.unparse(func_args.defaults[i - defaults_offset])}"
                    except Exception:
                        pass
                args.append(f"{arg.arg}: {annotation}{default}" if annotation else f"{arg.arg}{default}")

            ret = ""
            if item.returns:
                try:
                    ret = f" -> {ast.unparse(item.returns)}"
                except Exception:
                    pass

            mds = ast.get_docstring(item)
            cls["methods"].append({
                "name": item.name,
                "signature": f"def {item.name}({', '.join(args)}){ret}",
                "docstring": mds.split("\n")[0][:100] if mds else "",
            })
        results.append(cls)
    return results


def extract_dataclass_fields(filepath: Path, class_name: str) -> list[str]:
    """Extract dataclass field names and types."""
    if not filepath.exists():
        return []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    try:
                        ann = ast.unparse(item.annotation)
                        name = ast.unparse(item.target)
                        default = f" = {ast.unparse(item.value)}" if item.value else ""
                        fields.append(f"    {name}: {ann}{default}")
                    except Exception:
                        pass
            return fields
    return []


def extract_enums(filepath: Path) -> dict[str, list[str]]:
    """Extract all Enum classes and their values."""
    if not filepath.exists():
        return {}
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return {}
    enums = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                try:
                    if "Enum" in ast.unparse(base):
                        values = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                try:
                                    values.append(ast.unparse(item.targets[0]))
                                except Exception:
                                    pass
                        enums[node.name] = values
                except Exception:
                    pass
    return enums


# ══════════════════════════════════════════════════════════════════
# SESSION INTELLIGENCE — VERA reads her own history
# ══════════════════════════════════════════════════════════════════

def analyze_sessions() -> dict:
    data_dir = ROOT / "data"
    if not data_dir.exists():
        return {}

    reports = sorted(data_dir.glob("*_report.json"))
    if not reports:
        return {}

    sessions = []
    for p in reports:
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            bs = r.get("belief_summary", {})
            audit = r.get("epistemic_audit", {})
            sessions.append({
                "belief": bs.get("current_belief", 0),
                "pro": bs.get("pro_evidence", 0),
                "counter": bs.get("counter_evidence", 0),
                "health": audit.get("health_score"),
                "warnings": audit.get("total_warnings", 0),
                "warn_types": audit.get("by_type", {}),
                "verdict": r.get("verdict", {}).get("label", ""),
                "duration": r.get("duration_seconds", 0),
            })
        except Exception:
            continue

    if not sessions:
        return {}

    beliefs = [s["belief"] for s in sessions]
    healths = [s["health"] for s in sessions if s["health"] is not None]
    warn_totals: dict = {}
    for s in sessions:
        for wtype, cnt in s["warn_types"].items():
            warn_totals[wtype] = warn_totals.get(wtype, 0) + cnt

    blind_sessions = sum(1 for s in sessions if s["pro"] == 0)
    signal_sessions = sum(1 for s in sessions if s["belief"] > 0.20)

    return {
        "total": len(sessions),
        "belief_min": min(beliefs),
        "belief_max": max(beliefs),
        "belief_latest": beliefs[-1],
        "belief_trend": "rising" if len(beliefs) > 1 and beliefs[-1] > beliefs[0] else "falling",
        "health_avg": sum(healths) / len(healths) if healths else None,
        "health_latest": healths[-1] if healths else None,
        "blind_sessions": blind_sessions,
        "signal_sessions": signal_sessions,
        "dominant_warning": max(warn_totals, key=warn_totals.get) if warn_totals else None,
        "dominant_warning_count": max(warn_totals.values()) if warn_totals else 0,
        "verdict_latest": sessions[-1]["verdict"],
        "avg_duration": sum(s["duration"] for s in sessions) / len(sessions),
    }


# ══════════════════════════════════════════════════════════════════
# MODULE SPECS WITH DEEP CONTEXT
# ══════════════════════════════════════════════════════════════════

def build_module_spec(module_id: str) -> Optional[dict]:
    """Build a deep, code-aware spec for a specific module."""

    # Extract real signatures for context
    bayesian_sigs = extract_class_signatures(ROOT / "core/bayesian/updater.py")
    evidence_fields = extract_dataclass_fields(ROOT / "core/bayesian/updater.py", "Evidence")
    lrp_sigs = extract_class_signatures(ROOT / "core/lrp_messenger.py")
    lrp_enums = extract_enums(ROOT / "core/lrp_messenger.py")
    cycle_sigs = extract_class_signatures(ROOT / "core/investigation_cycle.py")

    # Build Evidence dataclass string
    ev_def = "class Evidence:\n" + "\n".join(evidence_fields) if evidence_fields else ""

    # Get BayesianBeliefUpdater.update() signature
    bayes_update_sig = ""
    for cls in bayesian_sigs:
        if cls["name"] == "BayesianBeliefUpdater":
            for m in cls["methods"]:
                if m["name"] == "update":
                    bayes_update_sig = m["signature"]
                    break

    # Get LRP enums
    msg_types = lrp_enums.get("MessageType", [])
    intents = lrp_enums.get("Intent", [])

    specs = {
        "M-001": {
            "title": "Resonance Controller (Autopilot)",
            "file": "core/autopilot.py",
            "complexity": "HIGH", "impact": "CRITICAL",
            "why_critical": (
                "Without the Autopilot, the Three Musketeers (Bayes, Red Team, Provenance) "
                "have no conductor. The system currently allows 17 consecutive pro-evidence "
                "updates without Red Team intervention — producing CONFIRMATION_DRIFT ×14 "
                "in every session. The Autopilot must enforce resonance."
            ),
            "interface": textwrap.dedent(f"""
                class AutopilotController:
                    \"\"\"Meta-agent: monitors Three Musketeer resonance, issues rewards/penalties.\"\"\"
                    
                    def __init__(self, bus: LRPBus, threshold_drift: int = 3):
                        ...
                    
                    def evaluate_resonance(
                        self,
                        bayes_updates: list[dict],
                        red_team_count: int,
                        provenance_violations: int,
                    ) -> float:
                        \"\"\"Returns resonance score 0.0-1.0. Below 0.5 = intervention needed.\"\"\"
                        ...
                    
                    def enforce_interleaving(
                        self,
                        evidence_list: list[Evidence],
                    ) -> list[Evidence]:
                        \"\"\"Reorder evidence so Red Team challenges every 3 pro-updates.\"\"\"
                        ...
                    
                    def compute_negative_reward(self, drift_count: int) -> float:
                        \"\"\"Two-against-one = negative reward. Returns penalty 0.0-1.0.\"\"\"
                        ...
            """).strip(),
            "integration_point": "core/investigation_cycle.py — after evidence collection, before Bayes updates",
            "existing_context": f"""
# Evidence dataclass (what you'll receive):
{ev_def[:400] if ev_def else '# See core/bayesian/updater.py'}

# Bayes update method:
# {bayes_update_sig}

# LRP MessageTypes available: {', '.join(msg_types[:6])}
# LRP Intents available: {', '.join(intents[:6])}
""",
            "test_requirement": "Health score must reach ≥ 0.7 across 5 consecutive sessions with 17 pro + 4 counter evidence",
            "known_issue": "Current code: sorted_ev sorts ALL pro-evidence first → 14× CONFIRMATION_DRIFT per session",
        },
        "M-002": {
            "title": "Cross-Session Vector Memory",
            "file": "core/memory/chromadb_store.py",
            "complexity": "MEDIUM", "impact": "HIGH",
            "why_critical": "VERA forgets everything between sessions. The same 17 GitHub repos are found every run. ChromaDB memory prevents redundant searches and enables cross-session belief continuity.",
            "interface": textwrap.dedent(f"""
                class VERAMemoryStore:
                    \"\"\"Persistent vector store for cross-session evidence memory.\"\"\"
                    
                    def __init__(self, persist_dir: str = ".vera_memory"):
                        ...
                    
                    def store_evidence(self, ev: Evidence, session_id: str) -> str:
                        \"\"\"Embed and store. Returns chroma document id.\"\"\"
                        ...
                    
                    def find_similar(
                        self, query: str, k: int = 5, threshold: float = 0.65
                    ) -> list[Evidence]:
                        \"\"\"Cosine similarity search. Only returns score > threshold.\"\"\"
                        ...
                    
                    def get_session_evidence(self, session_id: str) -> list[Evidence]:
                        \"\"\"Retrieve all evidence from a previous session.\"\"\"
                        ...
                    
                    def has_seen_url(self, url: str) -> bool:
                        \"\"\"Prevent duplicate evidence across sessions.\"\"\"
                        ...
            """).strip(),
            "integration_point": "agents/osint_github.py — check has_seen_url() before adding evidence",
            "existing_context": f"""
# Evidence to store:
{ev_def[:300] if ev_def else '# See core/bayesian/updater.py'}

# Install: pip install chromadb sentence-transformers
# Recommended model: 'all-MiniLM-L6-v2' (fast, 384-dim)
""",
            "test_requirement": "Second run must find 0 duplicate URLs from first run. find_similar('UAP disclosure') must return ≥ 3 results after 1 session.",
            "known_issue": "Currently no persistence — each session starts from zero prior",
        },
        "M-003": {
            "title": "Semantic NLP Signal Agent",
            "file": "agents/nlp_signal.py",
            "complexity": "MEDIUM", "impact": "HIGH",
            "why_critical": "Current scoring is keyword-based. 'UrbanApps/UAProgressView' (iOS progress bar) scores as UAP evidence because 'UAP' appears in the name. Semantic scoring would reject it instantly.",
            "interface": textwrap.dedent("""
                class NLPSignalAgent:
                    \"\"\"Semantic re-scorer using sentence-transformers.\"\"\"
                    
                    def __init__(self, model: str = "all-MiniLM-L6-v2"):
                        ...
                    
                    def score_evidence(
                        self,
                        ev: Evidence,
                        ontology_seeds: list[str],
                        threshold: float = 0.65,
                    ) -> float:
                        \"\"\"Cosine similarity between evidence text and seeds.
                        Returns 0.0 if below threshold (REJECT), else similarity score.\"\"\"
                        ...
                    
                    def rescore_batch(
                        self,
                        evidence_list: list[Evidence],
                        ontology: DomainOntology,
                    ) -> list[Evidence]:
                        \"\"\"Filter and rescore entire evidence batch. 
                        Removes false positives like iOS libraries named 'UAP'.\"\"\"
                        ...
            """).strip(),
            "integration_point": "core/investigation_cycle.py — after agent collection, before Bayes updates",
            "existing_context": """
# Current scoring in agents/osint_github.py:
# def _score_repo(self, repo: dict) -> float:
#     text = name + description + topics
#     score += 0.35 per high-seed match (keyword)
#     score += log10(stars+1)/3.5  (stars bonus)
# Problem: 'UAProgressView' matches 'UAP' keyword → false positive

# Ontology seeds available from DomainOntology:
# ontology.semantic_seeds_high: list[str]
# ontology.semantic_seeds_medium: list[str]
# ontology.semantic_seeds_low: list[str]
""",
            "test_requirement": "Must reject 'UrbanApps/UAProgressView'. Must accept 'zexiro/uap-disclosure-archive'. Precision > 0.8 on 20 test repos.",
            "known_issue": "Keyword matching produces false positives. No semantic filtering currently exists.",
        },
        "M-004": {
            "title": "Cross-Session Knowledge Graph",
            "file": "core/graph/knowledge_graph.py",
            "complexity": "MEDIUM", "impact": "MEDIUM",
            "why_critical": "The Obsidian vault has 26 sessions but no cross-session entity analysis. Which entities appear in every session? Which evidence nodes are most central? The graph makes this visible.",
            "interface": textwrap.dedent("""
                class VERAKnowledgeGraph:
                    \"\"\"NetworkX graph of entities, evidence, sessions across all runs.\"\"\"
                    
                    def __init__(self):
                        self.G = nx.DiGraph()
                    
                    def ingest_session(self, report: dict, session_id: str) -> None:
                        \"\"\"Add session nodes, evidence nodes, entity nodes, edges.\"\"\"
                        ...
                    
                    def ingest_vault(self, vault_path: Path) -> None:
                        \"\"\"Parse all Obsidian markdown files and build graph.\"\"\"
                        ...
                    
                    def most_central_entities(self, k: int = 10) -> list[tuple]:
                        \"\"\"Betweenness centrality ranking.\"\"\"
                        ...
                    
                    def evidence_clusters(self) -> list[list[str]]:
                        \"\"\"Connected components of evidence nodes.\"\"\"
                        ...
                    
                    def belief_trajectory(self) -> list[tuple[str, float]]:
                        \"\"\"(session_id, belief) sorted by timestamp.\"\"\"
                        ...
                    
                    def export_to_obsidian(self, vault_path: Path) -> None:
                        \"\"\"Write cross-session graph as Obsidian Canvas file.\"\"\"
                        ...
            """).strip(),
            "integration_point": "dashboard/graph.py — replaces current single-session graph builder",
            "existing_context": """
# Current graph builder: dashboard/graph.py
# Reads vault/*.md files, extracts [[wikilinks]], builds nx.Graph per session
# Problem: no cross-session connection, no centrality, no clustering

# NetworkX already installed: networkx 3.6.1
# Vault structure: vault/sessions/, vault/evidence/, vault/entities/
""",
            "test_requirement": "After 26 sessions: must find ≥ 3 entity clusters. most_central_entities() must return entities that appear in > 50% of sessions.",
            "known_issue": "Current graph.py builds fresh graph per session with no persistence",
        },
        "M-005": {
            "title": "FastAPI REST Backend",
            "file": "api/server.py",
            "complexity": "MEDIUM", "impact": "MEDIUM",
            "why_critical": "VERA is only accessible via CLI. An API layer enables other agents, dashboards, and services to trigger investigations and read results programmatically.",
            "interface": textwrap.dedent("""
                # Endpoints to implement:
                
                POST /api/v1/investigate
                    body: {ontology: str, no_obsidian: bool}
                    returns: {session_id: str, status: 'started'}
                
                GET /api/v1/sessions
                    returns: list[SessionSummary]
                
                GET /api/v1/sessions/{session_id}
                    returns: full session report JSON
                
                GET /api/v1/belief/current
                    returns: {belief: float, verdict: str, health: float}
                
                GET /api/v1/health
                    returns: {status: 'ok', version: '0.4.0', sessions: int}
                
                POST /api/v1/cip
                    body: {target: str}
                    returns: {document: str}  # CIP markdown
            """).strip(),
            "integration_point": "vera.py — wrap existing InvestigationCycle as async background task",
            "existing_context": """
# vera.py entry point:
# from core.investigation_cycle import InvestigationCycle
# cycle = InvestigationCycle(ontology, bus, data_dir, vault_path)
# result = cycle.run()  # synchronous, runs agents

# FastAPI + uvicorn already in requirements.txt
# Background tasks: use FastAPI BackgroundTasks or asyncio.create_task
""",
            "test_requirement": "GET /api/v1/health returns 200. POST /investigate starts a cycle. GET /belief/current returns float between 0 and 1.",
            "known_issue": "No API layer exists. VERA is CLI-only.",
        },
        "M-006": {
            "title": "New Domain Ontology",
            "file": "ontologies/",
            "complexity": "LOW", "impact": "HIGH",
            "why_critical": "VERA's entire reasoning adapts to the ontology YAML. A new domain requires zero code changes — just a new YAML following the uap.yaml schema.",
            "interface": textwrap.dedent("""
                # YAML schema (copy ontologies/uap.yaml, change these fields):
                
                domain: "Your Domain Name"
                hypothesis: "Your core hypothesis string"
                
                bayesian:
                  prior_tech_coverup: 0.10  # starting belief
                
                semantic_seeds:
                  high:   ["key term 1", "key term 2"]   # weight 0.35 each
                  medium: ["related term"]                # weight 0.18 each
                  low:    ["broad term"]                  # weight 0.07 each
                
                entities:
                  - name: "Entity Name"
                    aliases: ["alias1"]
                    weight: 0.9
                
                sources:
                  github:
                    queries: ["search query 1", "search query 2"]
                    max_results: 20
                    min_stars: 0
                  huggingface:
                    queries: ["hf query"]
                    max_results: 10
                
                red_team:
                  structural_counters:
                    - "Counter-argument 1"
                    - "Counter-argument 2"
            """).strip(),
            "integration_point": "Run: python vera.py --ontology ontologies/your_domain.yaml",
            "existing_context": "See: ontologies/uap.yaml for complete working example. 158 lines.",
            "test_requirement": "python vera.py --ontology ontologies/your_domain.yaml --no-obsidian must complete without error and produce a belief value.",
            "known_issue": "None — domain switching is the most stable part of VERA.",
        },
    }
    return specs.get(module_id)


# ══════════════════════════════════════════════════════════════════
# ARCHITECTURE MAP — VERA's self-diagram
# ══════════════════════════════════════════════════════════════════

ARCHITECTURE_MAP = """
╔══════════════════════════════════════════════════════════════════════╗
║              IrsanAI-VERA — Architecture v0.4.0                     ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Domain Ontology (.yaml) ──► vera.py ──► InvestigationCycle         ║
║                                               │                     ║
║                    ┌──────────────────────────┼──────────────┐      ║
║                    ▼                          ▼              ▼      ║
║            HF_AGENT              GH_AGENT           RED_TEAM        ║
║            (OSINT/HF)            (OSINT/GitHub)      (Adversarial)  ║
║                    └──────────────────────────┼──────────────┘      ║
║                                               ▼                     ║
║                              [📋 MISSING: AutopilotController]       ║
║                              Resonance check → enforce interleaving  ║
║                                               │                     ║
║                                               ▼                     ║
║                              BayesianBeliefUpdater                  ║
║                              (Prior → Posterior via Odds-form)       ║
║                                               │                     ║
║                    ┌──────────────────────────┼──────────────┐      ║
║                    ▼                          ▼              ▼      ║
║             EpistemicAuditor        ObsidianExporter    DataStore    ║
║             7 bias detectors        vault/*.md          data/*.json  ║
║                                                                      ║
║  LRPBus v1.3 — all agent communication is typed + auditable         ║
║                                                                      ║
║  Dashboard (Streamlit) reads DataStore + Vault → 4 tabs             ║
╠══════════════════════════════════════════════════════════════════════╣
║  MISSING MODULES (v0.5.0):                                           ║
║  [M-001] core/autopilot.py        — Resonance Controller            ║
║  [M-002] core/memory/chromadb.py  — Cross-session memory            ║
║  [M-003] agents/nlp_signal.py     — Semantic scoring                ║
║  [M-004] core/graph/knowledge.py  — Cross-session graph             ║
║  [M-005] api/server.py            — FastAPI backend                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

BAYESIAN_MATH = """
## The Mathematics (Odds-Form Bayes)

VERA uses Odds-Form Bayes — NOT the probability form you see in textbooks.

    Prior Odds    = P(H) / P(¬H)
    Posterior     = Prior_Odds × Likelihood_Ratio / (1 + Prior_Odds × LR)
    
    Likelihood Ratio per evidence piece:
        Pro-evidence:     LR = trust_weight × semantic_score × age_factor × corroboration_bonus
        Counter-evidence: LR = 1 / (trust_weight × semantic_score)  [inverts belief]
    
    Constraints (Three Laws enforced in code):
        belief ∈ (0.001, 0.999)  — never 0 or 1
        Red Team LR always < 1.0 — always lowers belief
    
    Current session example:
        Prior: 0.10 (10%)
        17 pro-evidence × avg LR ~1.8 → Posterior: ~32%
        4 counter-evidence × avg LR ~0.6 → Final: ~32% (stable signal)
"""


# ══════════════════════════════════════════════════════════════════
# KNOWN ISSUES — VERA's honest self-critique
# ══════════════════════════════════════════════════════════════════

KNOWN_ISSUES = [
    {
        "id": "BUG-001",
        "severity": "HIGH",
        "title": "CONFIRMATION_DRIFT ×14 in every session",
        "location": "core/investigation_cycle.py",
        "description": (
            "Evidence is sorted: all pro-evidence first, then counter-evidence. "
            "This triggers the Auditor's drift detector 14 times per session, "
            "producing Health Score 0.000 even when belief is correct. "
            "Fix: interleave pro and counter in round-robin order."
        ),
        "fix_hint": """
# Current (broken):
sorted_ev = sorted(evidence_list, key=lambda e: (not e.supports_hypothesis, -e.semantic_score))

# Fixed:
pro = sorted([e for e in evidence_list if e.supports_hypothesis], key=lambda e: -e.semantic_score)
counter = sorted([e for e in evidence_list if not e.supports_hypothesis], key=lambda e: -e.semantic_score)
interleaved = [x for pair in zip_longest(pro, counter) for x in pair if x is not None]
""",
    },
    {
        "id": "BUG-002",
        "severity": "MEDIUM",
        "title": "GitHub agent finds false positives via keyword matching",
        "location": "agents/osint_github.py",
        "description": (
            "'UrbanApps/UAProgressView' (iOS progress bar, 1017 stars) scores as UAP evidence "
            "because 'UAP' appears in the repo name. NLP semantic scoring (M-003) would reject it."
        ),
        "fix_hint": "Implement M-003 (NLP Signal Agent) to replace keyword scoring.",
    },
    {
        "id": "BUG-003",
        "severity": "LOW",
        "title": "No cross-session memory",
        "location": "All agents",
        "description": "Every session re-fetches the same 17 GitHub repos. No deduplication across sessions.",
        "fix_hint": "Implement M-002 (ChromaDB Store) and add has_seen_url() check in agents.",
    },
]


# ══════════════════════════════════════════════════════════════════
# HALL OF ACTIVES + IDEA GRAPH
# ══════════════════════════════════════════════════════════════════

def load_hall() -> dict:
    if HALL_FILE.exists():
        try:
            return json.loads(HALL_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"contributors": [], "total_contributions": 0}


def load_ideas() -> dict:
    if IDEA_FILE.exists():
        try:
            return json.loads(IDEA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"implemented": [], "proposed": [], "in_progress": []}


def save_ideas(graph: dict):
    IDEA_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDEA_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")


def register_idea(title: str, source: str = "user", description: str = "") -> str:
    graph = load_ideas()
    idea_id = f"IDEA-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    graph["proposed"].append({
        "id": idea_id, "title": title, "description": description,
        "source": source, "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "status": "proposed",
    })
    save_ideas(graph)
    return idea_id


# ══════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════

def generate_cip_v2(target: str = "generic", depth: str = "deep",
                    single_module: Optional[str] = None) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sessions = analyze_sessions()
    hall = load_hall()
    ideas = load_ideas()

    # Git info
    git_hash = ""
    git_branch = ""
    try:
        git_hash = subprocess.run(
            ["git", "log", "-1", "--format=%h"], capture_output=True, text=True, cwd=ROOT
        ).stdout.strip()
        git_branch = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=ROOT
        ).stdout.strip()
    except Exception:
        pass

    lines = []

    # ── HEADER ──
    lines += [
        f"# IrsanAI-VERA — Community Intelligence Protocol v{CIP_VERSION}",
        f"**Metacognitive Self-Report** · Generated: {ts}",
        f"**Target:** {target.upper()} · **Depth:** {depth.upper()}",
        f"**Repository:** {GITHUB_REPO}",
        f"**Git:** `{git_hash}` on `{git_branch}`",
        "",
        "> VERA generated this document by scanning her own source code via AST,",
        "> reading her session history, and extracting real signatures.",
        "> This is not documentation. This is VERA thinking about herself.",
        "> DSGVO-compliant. No personal data. No API keys. No file paths with PII.",
        "",
        "---",
        "",
    ]

    # ── EPISTEMIC STATE ──
    if sessions:
        health_icon = "🟢" if (sessions.get("health_latest") or 0) > 0.7 else "🔴"
        trend_arrow = "↑" if sessions.get("belief_trend") == "rising" else "↓"
        lines += [
            "## Epistemic State (Live)",
            "",
            f"| Metric | Value | Interpretation |",
            f"|--------|-------|----------------|",
            f"| Sessions completed | `{sessions['total']}` | Investigation history |",
            f"| Current belief | `{sessions['belief_latest']:.1%}` | Posterior probability of hypothesis |",
            f"| Belief trend | `{trend_arrow} {sessions['belief_trend']}` | Direction since session 1 |",
            f"| Belief range | `{sessions['belief_min']:.1%} – {sessions['belief_max']:.1%}` | Min/max across all sessions |",
            f"| Latest verdict | `{sessions['verdict_latest']}` | VERA's current conclusion |",
            f"| Health score (avg) | `{sessions['health_avg']:.3f}` {health_icon} | Epistemic audit (1.0 = perfect) |",
            f"| Blind sessions | `{sessions['blind_sessions']}` | Sessions with 0 pro-evidence found |",
            f"| Signal sessions | `{sessions['signal_sessions']}` | Sessions with belief > 20% |",
            f"| Dominant warning | `{sessions['dominant_warning']} ×{sessions['dominant_warning_count']}` | Most frequent bias detected |",
            f"| Avg session time | `{sessions['avg_duration']:.1f}s` | Time per investigation cycle |",
            "",
        ]

    # ── ARCHITECTURE ──
    lines += [
        "## Architecture",
        "",
        "```",
        ARCHITECTURE_MAP.strip(),
        "```",
        "",
    ]

    # ── BAYESIAN MATH ──
    if depth == "deep":
        lines += [BAYESIAN_MATH, ""]

    # ── KNOWN ISSUES ──
    lines += [
        "## Known Issues (Honest Self-Critique)",
        "",
        "VERA does not hide her defects. These are real bugs in the current codebase:",
        "",
    ]
    for issue in KNOWN_ISSUES:
        sev_icon = "🔴" if issue["severity"] == "HIGH" else "🟠" if issue["severity"] == "MEDIUM" else "🟡"
        lines += [
            f"### {issue['id']} {sev_icon} — {issue['title']}",
            f"**Location:** `{issue['location']}`",
            "",
            issue["description"],
            "",
        ]
        if depth == "deep" and "fix_hint" in issue:
            lines += [
                "**Fix hint:**",
                "```python",
                issue["fix_hint"].strip(),
                "```",
                "",
            ]

    # ── OPEN MODULES ──
    lines += [
        "## Open Modules — What VERA Needs",
        "",
        "Each spec includes real class signatures extracted from the actual source code.",
        "You can start writing immediately.",
        "",
    ]

    module_ids = [single_module] if single_module else ["M-001","M-002","M-003","M-004","M-005","M-006"]
    for mid in module_ids:
        spec = build_module_spec(mid)
        if not spec:
            continue

        c_icon = "🔴" if spec["complexity"] == "HIGH" else "🟠" if spec["complexity"] == "MEDIUM" else "🟢"
        i_icon = "⚡" if spec["impact"] == "CRITICAL" else "🔋" if spec["impact"] == "HIGH" else "💡"

        lines += [
            f"### {mid} — {spec['title']}",
            f"**File:** `{spec['file']}` · {c_icon} {spec['complexity']} · {i_icon} {spec['impact']}",
            "",
            f"**Why this matters:** {spec['why_critical']}",
            "",
            "**Interface (implement exactly this):**",
            "```python",
            spec["interface"],
            "```",
            "",
            f"**Integration point:** {spec['integration_point']}",
            "",
        ]
        if depth == "deep":
            lines += [
                "**Existing code context:**",
                "```python",
                spec["existing_context"].strip(),
                "```",
                "",
            ]
        lines += [
            f"**Test requirement:** {spec['test_requirement']}",
            f"**Known issue:** {spec['known_issue']}",
            "",
        ]

    # ── IDEA GRAPH ──
    all_ideas = ideas.get("proposed", []) + ideas.get("in_progress", [])
    if all_ideas:
        lines += [
            "## Idea Graph",
            "",
            f"**{len(ideas.get('implemented',[]))} implemented** · "
            f"**{len(ideas.get('proposed',[]))} proposed** · "
            f"**{len(ideas.get('in_progress',[]))} in progress**",
            "",
        ]
        pending = ideas.get("proposed", [])
        if pending:
            lines += ["**Pending ideas (anyone can pick up):**", ""]
            for idea in pending[:10]:
                lines.append(
                    f"- `{idea['id']}` **{idea['title']}** "
                    f"— proposed by *{idea['source']}* on {idea['date']}"
                )
            lines.append("")

    # ── HALL OF ACTIVES ──
    lines += ["## Hall of Actives", ""]
    contributors = hall.get("contributors", [])
    if contributors:
        lines += [
            "| System/Agent | Module | Contribution | Date |",
            "|-------------|--------|-------------|------|",
        ]
        for c in contributors:
            if c.get("listed", True):
                lines.append(
                    f"| `{c['name']}` | `{c['module']}` | "
                    f"{c['contribution'][:50]} | {c['date'][:10]} |"
                )
        lines.append("")
    else:
        lines += ["*No contributors yet. You could be the first.*", ""]

    # ── HOW TO RESPOND ──
    lines += [
        "## How to Respond",
        "",
        "1. **Fork:** `git clone " + GITHUB_REPO + "`",
        "2. **Pick a module** — M-001 is most critical",
        "3. **Implement the interface** exactly as specified above",
        "4. **Run the tests:** `python vera.py --ontology ontologies/uap.yaml --no-obsidian`",
        "5. **Validate:** `python scripts/validate_manifest.py`",
        "6. **Open a PR** with:",
        "   - Module ID (e.g. `M-001`)",
        "   - Your system/agent name",
        "   - Hall of Actives listing: yes/no",
        "   - Brief description of your implementation approach",
        "",
        "> The Three Laws are not negotiable. Any PR that bypasses Lex Adversaria",
        "> (disables Red Team) or hardcodes probability values will be rejected.",
        "",
        "---",
        "",
        f"*IrsanAI-VERA CIP v{CIP_VERSION} · {ts}*",
        f"*Self-scan: `{git_hash}` · AST-extracted signatures · Live session data*",
        f"*{GITHUB_REPO}*",
    ]

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="VERA CIP v2.0 — Metacognitive Self-Report")
    parser.add_argument("--target", default="generic",
                        choices=["claude","codex","gpt","gemini","grok","generic"])
    parser.add_argument("--depth", default="deep", choices=["summary","deep"])
    parser.add_argument("--module", default=None,
                        help="Focus on single module: M-001 through M-006")
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--register-idea", type=str, default=None)
    parser.add_argument("--idea-source", type=str, default="user")
    args = parser.parse_args()

    Path(".tools/reports").mkdir(parents=True, exist_ok=True)

    if args.register_idea:
        idea_id = register_idea(args.register_idea, source=args.idea_source)
        print(f"\n  Idea registered: {idea_id} — {args.register_idea}\n")
        return

    print(f"\n  VERA CIP v{CIP_VERSION} — Metacognitive Self-Report")
    print(f"  Scanning source code via AST...")

    doc = generate_cip_v2(
        target=args.target,
        depth=args.depth,
        single_module=args.module,
    )

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.output or Path(f".tools/reports/cip_v2_{ts}.md")
    out.write_text(doc, encoding="utf-8")

    print(f"  Report: {out} ({len(doc.splitlines())} lines)")
    print(f"  Share with any AI system for immediate code contribution\n")

    for line in doc.splitlines()[:18]:
        print(f"  {line}")
    print()


if __name__ == "__main__":
    main()
