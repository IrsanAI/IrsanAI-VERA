# IrsanAI-VERA
### Veridical Evidence Reasoning Architecture

> *A domain-agnostic, epistemically honest multi-agent engine that distills structured, traceable beliefs from heterogeneous, adversarial information spaces.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![IrsanAI Ecosystem](https://img.shields.io/badge/IrsanAI-Ecosystem-purple)](https://github.com/IrsanAI)

---

## What is VERA?

VERA is not an OSINT scraper. It is not a search engine. It is an **Automated Epistemology Engine** — a system that mimics what rigorous investigators, scientists, and lawyers do manually:

1. **Collect** evidence from heterogeneous sources
2. **Weight** each piece by credibility and relevance
3. **Challenge** every conclusion with adversarial counter-evidence
4. **Update** beliefs using Bayesian probability — never hardcoded values
5. **Document** the full provenance chain of every claim
6. **Persist** knowledge across sessions as a living knowledge graph

The UAP/disclosure domain is the proof-of-concept testcase — chosen because it is the *hardest* possible domain: maximally adversarial, deliberately obscured, multi-source. If VERA works here, it works everywhere.

---

## Core Design Principles

| Principle | Meaning |
|-----------|---------|
| **Epistemic Honesty** | No probability value without traceable evidence. Ever. |
| **Adversarial Balance** | Every claim is actively challenged by a Red Team Agent |
| **Provenance Chain** | Every conclusion links back: Claim → Evidence[] → Source + Method + Timestamp |
| **Domain Agnosticism** | Swap `ontologies/uap.yaml` for `ontologies/oncology.yaml` — everything else runs identically |
| **Persistent Memory** | ChromaDB vector store — the system remembers across sessions |
| **Human Readability** | Obsidian vault export — the knowledge graph as navigable markdown |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VERA Core Loop                       │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  Ontology    │───▶│  Agent       │                  │
│  │  Loader      │    │  Orchestrator │                  │
│  │  (.yaml)     │    └──────┬────────┘                  │
│  └──────────────┘           │                           │
│                    ┌────────┼────────┐                  │
│                    ▼        ▼        ▼                  │
│             ┌──────────┐ ┌──────┐ ┌──────────────┐      │
│             │  OSINT   │ │ NLP  │ │  Adversarial │      │
│             │  Agents  │ │Signal│ │  Red Team    │      │ 
│             └────┬─────┘ └──┬───┘ └──────┬───────┘      │ 
│                  └──────────┼─────────────┘             │
│                             ▼                           │
│                    ┌────────────────┐                   │
│                    │ Bayesian Belief│                   │
│                    │    Updater     │                   │
│                    └───────┬────────┘                   │
│                            │                            │
│               ┌────────────┼──────────────┐             │
│               ▼            ▼              ▼             │
│        ┌──────────┐ ┌──────────┐ ┌──────────────┐       │  
│        │ ChromaDB │ │NetworkX  │ │  Obsidian    │       │
│        │  Memory  │ │  Graph   │ │  Vault Export│       │
│        └──────────┘ └──────────┘ └──────────────┘       │
│                                                         │
│                    ┌────────────┐                       │
│                    │  LRP v1.3  │ ← Inter-Agent Protocol│
│                    │  Messages  │                       │
│                    └────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

---

## Module Overview

### `core/`

| Module | Purpose |
|--------|---------|
| `core/bayesian/updater.py` | Bayesian Belief Network — all probability values come from here |
| `core/bayesian/evidence.py` | Evidence dataclass with provenance chain |
| `core/graph/knowledge_graph.py` | NetworkX graph — entities, relationships, weights |
| `core/graph/obsidian_exporter.py` | Converts graph to Obsidian-compatible markdown notes |
| `core/lrp_messenger.py` | IrsanAI-LRP v1.3 inter-agent message format |
| `core/autopilot.py` | RL-based strategy selector (epsilon-greedy + Q-learning) |
| `core/env_adapter.py` | Hardware-aware configuration |

### `agents/`

| Agent | Purpose |
|-------|---------|
| `agents/osint_github.py` | GitHub repository intelligence crawler |
| `agents/osint_huggingface.py` | HuggingFace dataset semantic search |
| `agents/nlp_signal.py` | Sentence-transformer semantic density analysis |
| `agents/red_team.py` | **Adversarial agent — actively seeks counter-evidence** |
| `agents/news_crawler.py` | RSS/public news feeds (real, not simulated) |

### `ontologies/`

YAML files that define a domain. Swap to change the entire system's focus.

```yaml
# ontologies/uap.yaml (example)
domain: "UAP Disclosure"
entities:
  - AARO
  - Pentagon
  - FOIA
source_weights:
  government_document: 0.9
  whistleblower: 0.4
  news_article: 0.3
prior_probability: 0.15  # Starting point — low until evidence arrives
keywords_semantic:
  - "special access program"
  - "non-human intelligence"
  - "unacknowledged"
```

### `obsidian_writer/`

Automatically generates a structured Obsidian vault from each investigation cycle:

```
vault/
├── entities/
│   ├── AARO.md          ← All findings linked to AARO
│   ├── Pentagon.md
├── evidence/
│   ├── EVD-20260414-001.md  ← Individual evidence notes
├── sessions/
│   ├── 2026-04-14.md    ← Daily session summary
└── _index.md            ← Living investigation overview
```

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/IrsanAI/IrsanAI-VERA.git
cd IrsanAI-VERA

# 2. Install
pip install -e ".[dev]"

# 3. Configure your domain
cp ontologies/uap.yaml ontologies/my_domain.yaml
# Edit my_domain.yaml

# 4. Run
python vera.py --ontology ontologies/uap.yaml

# 5. View Knowledge Graph (Obsidian)
# Open the /vault folder in Obsidian

# 6. Dashboard
streamlit run dashboard/app.py
```

---

## Key Difference from Other OSINT Tools

| Feature | VERA | Typical OSINT Tool |
|---------|------|-------------------|
| Probability source | Bayesian updates from real evidence | Hardcoded or heuristic |
| Counter-evidence | Built-in Red Team Agent | None |
| Memory | ChromaDB cross-session | Per-run only |
| Knowledge graph | NetworkX + Obsidian export | None |
| Domain change | Swap one YAML file | Rewrite entire tool |
| Audit trail | Full provenance chain | Log files |
| Inter-agent protocol | IrsanAI-LRP v1.3 | Custom or none |

---

## Domain Applications

The UAP domain is the proof-of-concept. The same architecture applies to:

- **Medical research**: Drug efficacy evidence synthesis, clinical trial anomaly detection
- **Financial crime**: Structured money flow analysis, regulatory filing anomalies
- **Cybersecurity**: Threat intelligence aggregation, zero-day pattern detection
- **Scientific fraud**: Replication crisis analysis, citation network anomalies
- **Legal due diligence**: Contract risk evidence chains, regulatory exposure mapping
- **Climate science**: Multi-source sensor data synthesis, model discrepancy analysis

---

## IrsanAI Ecosystem Integration

VERA uses **IrsanAI-LRP v1.3** as the inter-agent communication protocol. All agent messages are LRP-formatted with intent scoring, confidence levels, and token budgets — making the entire system auditable and compatible with other IrsanAI ecosystem tools.

---

## Project Status

| Component | Status |
|-----------|--------|
| Project skeleton | ✅ Complete |
| Ontology loader | 🔨 In development |
| Bayesian core | 🔨 In development |
| OSINT agents | 🔨 In development |
| Red Team Agent | 📋 Planned |
| ChromaDB memory | 📋 Planned |
| Obsidian exporter | 📋 Planned |
| LRP integration | 📋 Planned |
| Dashboard | 📋 Planned |

---

## Legacy

The `legacy/` folder contains the prototype versions (v1.0–v1.6) that led to this architecture. They are preserved as archaeological record of the design evolution.

---

## License

MIT — IrsanAI Ecosystem 2026
