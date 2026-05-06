<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          V E R A                                             ║
║          Veridical Evidence Reasoning Architecture           ║
║                                                              ║
║          The world's first open-source                       ║
║          Automated Epistemology Engine                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![IrsanAI Ecosystem](https://img.shields.io/badge/IrsanAI-Ecosystem-purple?style=for-the-badge)](https://github.com/IrsanAI)
[![Version](https://img.shields.io/badge/Version-0.4.0-cyan?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()

🌐 **Language:** [Deutsch](#deutsch) | [English](#english)

---

*"Not another AI that collects information.*
*A machine that earns the right to believe."*

</div>

---

<a name="english"></a>

## What is VERA?

VERA is not an OSINT tool. It is not a search engine. It is not a chatbot wrapper.

**VERA is an Automated Epistemology Engine** — a system that does what rigorous scientists, intelligence analysts, and judges do manually:

1. **Collect** evidence from real, heterogeneous sources
2. **Challenge** every conclusion with an adversarial Red Team Agent
3. **Update** beliefs mathematically via Bayesian probability — never hardcoded values
4. **Document** the full provenance chain of every single claim
5. **Monitor** its own reasoning process for 7 types of cognitive bias
6. **Export** everything into a navigable Obsidian Knowledge Graph

**The UAP/Disclosure domain is the proof-of-concept stress test.**
If VERA works in the world's most adversarial information environment, it works everywhere.

---

## The Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERA Core Loop                               │
│                                                                 │
│  Domain Ontology (.yaml) ──► Agent Orchestrator                 │
│                                    │                           │
│              ┌─────────────────────┼─────────────────┐         │
│              ▼                     ▼                  ▼         │
│         HF Agent           GitHub Agent         Red Team        │
│         (OSINT)            (OSINT)              (Adversarial)   │
│              └─────────────────────┼─────────────────┘         │
│                                    ▼                           │
│                        Bayesian Belief Updater                  │
│                        (Every value = real evidence)            │
│                                    │                           │
│                ┌───────────────────┼──────────────┐            │
│                ▼                   ▼              ▼            │
│           ChromaDB           NetworkX         Obsidian         │
│           (Memory)           (Graph)          (Vault)          │
│                                    │                           │
│                        Epistemic Auditor                        │
│                        (7 Bias Detectors · Health Score)        │
│                                    │                           │
│                     IrsanAI-LRP v1.3 Protocol                   │
│                     (All agent comms are auditable)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Three Musketeers (Core Design Principle)

Inspired by the Israeli intelligence technique *"Ipcha Mistabra"* (The opposite is logical) — the same method that gave rise to Israel's Devil's Advocate Office after the 1973 Yom Kippur War:

| Unit | Module | Role |
|------|--------|------|
| ⚖️ **Bayes** | `core/bayesian/updater.py` | Mathematical conscience — all probabilities |
| ⚔️ **Adversary** | `agents/red_team.py` | Active counter-evidence seeker |
| 🔗 **Provenance** | `core/bayesian/evidence.py` | Chain of custody for every claim |

**Golden Rule:** No unit can achieve majority. Two against one = negative reward = system degradation. Only resonance of all three produces valid knowledge.

---

## Three Golden Protocols

These are hardcoded into the architecture — not configurable, not bypassable:

**Lex Bayesian** — No belief can reach 1.0 or 0.0. Absolute certainty is mathematically forbidden.

**Lex Adversaria** — Red Team resources scale proportionally with belief confidence. The more certain the system, the harder it attacks itself.

**Lex Proventia** — Any information without a verifiable provenance chain receives a trust multiplier of zero. No source = no influence.

---

## Domain Agnosticism

Swap one YAML file. The entire system changes domain.

```yaml
# ontologies/uap.yaml         → UAP Disclosure (current)
# ontologies/oncology.yaml    → Medical research fraud detection
# ontologies/finance.yaml     → Financial crime analysis
# ontologies/climate.yaml     → Climate data synthesis
# ontologies/legal.yaml       → Legal due diligence
```

No code changes. Same Bayesian core. Same Red Team. Same audit trail.

---

## What's Built (v0.4.0)

| Module | Status | Note |
|--------|--------|------|
| Ontology Loader | ✅ Complete | YAML-driven domain switching |
| Bayesian Core | ✅ Complete | True Bayes updates, no hardcoded values |
| OSINT Agents (HF + GitHub) | ✅ Complete | Real API integration, funnel strategy |
| Red Team Agent | ✅ Complete | Adversarial counter-evidence, lowers belief |
| Obsidian Exporter | ✅ Complete | Auto-generated knowledge vault |
| LRP v1.3 Protocol | ✅ Complete | Auditable inter-agent messaging |
| Epistemic Auditor | ✅ Complete | 7 bias detectors, health scores |
| Epistemic Ops Dashboard | ✅ Complete | Dark-mode operations center |
| PatchBot | ✅ Complete | Claude↔Local bridge for structured patches |
| Preflight Scanner | ✅ Complete | Full system intelligence report |
| ChromaDB Memory | 📋 Planned | v0.5.0 |
| NLP Signal Agent | 📋 Planned | v0.5.0 |
| NetworkX Knowledge Graph | 📋 Planned | v0.5.0 |
| Autopilot (Resonance Controller) | 📋 Planned | v0.5.0 |
| FastAPI Backend | 📋 Planned | v0.6.0 |

---

## Quickstart

```bash
git clone https://github.com/IrsanAI/IrsanAI-VERA.git
cd IrsanAI-VERA

pip install requests pyyaml psutil streamlit plotly pandas networkx

cp .env.example .env
# Add your GITHUB_TOKEN to .env

python vera.py --ontology ontologies/uap.yaml
streamlit run dashboard/app.py
```

---

## The IrsanAI Toolchain (Local Only · Never on GitHub)

These tools bridge the gap between Claude (online LLM) and your local environment:

| Tool | Purpose |
|------|---------|
| `irsanai_preflight.py` | Full system scan → report for Claude |
| `irsanai_patchbot.py` | Applies structured VERA_PATCH instructions |
| `irsanai_patchbot_status.py` | Generates LLM-ready status snapshot |

**Workflow:** Preflight scans → Claude analyzes → PatchBot applies → VERA runs

---

## The Vision (What Community Can Build)

See [VISION.md](VISION.md) for the complete roadmap of what becomes possible when this foundation is extended by the community.

The short version: adaptive authentication, RL-driven immersive UX, real-time 3D knowledge graph exploration, global unique keys per investigation, cross-user distributed learning. Zero operational cost for the open core. Community decides what to build on top.

---

## Roadmap

| Feature | Resonanz | Chemie | Coach |
|---------|----------|--------|-------|
| Autopilot (Resonance Controller) | `92/100` 🟩🟩🟩🟩⬜ | `95/100` 🟩🟩🟩🟩🟩 | Three Musketeers need a conductor |
| ChromaDB Cross-Session Memory | `88/100` 🟩🟩🟩🟩⬜ | `90/100` 🟩🟩🟩🟩⬜ | Without memory VERA forgets everything |
| NLP Semantic Scoring | `85/100` 🟩🟩🟩🟩⬜ | `88/100` 🟩🟩🟩🟩⬜ | Keyword → concept understanding |
| NetworkX Knowledge Graph | `83/100` 🟩🟩🟩🟩⬜ | `86/100` 🟩🟩🟩🟩⬜ | Entities connect across sessions |
| Extended Ontology v2 | `95/100` 🟩🟩🟩🟩🟩 | `95/100` 🟩🟩🟩🟩🟩 | Falsification criteria per entity |
| FastAPI Backend | `78/100` 🟩🟩🟩⬜⬜ | `82/100` 🟩🟩🟩🟩⬜ | API layer enables everything else |
| Docker Deployment | `72/100` 🟩🟩🟩⬜⬜ | `80/100` 🟩🟩🟩🟩⬜ | One-command self-hosting |
| HuggingFace Spaces Demo | `90/100` 🟩🟩🟩🟩⬜ | `88/100` 🟩🟩🟩🟩⬜ | Free global visibility |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — every module in the roadmap is an open invitation.

---

## IrsanAI Ecosystem

VERA is part of a larger ecosystem:

- **[irsanai-mom4ai-forge](https://github.com/IrsanAI/irsanai-mom4ai-forge)** — Evolutionary bio-inspired neural network skeleton generator
- **[IrsanAI-LRP](https://github.com/IrsanAI/IrsanAI-LRP)** — Language Request Protocol v1.3
- **IrsanAI-VERA** — You are here

---

## Support

VERA is free. Forever. For everyone.

If it brought you value — a discovery, a better decision, a new way of thinking about truth — you're welcome to say thank you:

*PayPal · Revolut · IBAN — contact via GitHub Issues*

But build first. Share first. The world benefits first.

---

<a name="deutsch"></a>

## Was ist VERA? (Deutsch)

VERA ist kein OSINT-Tool. Kein Suchwerkzeug. Kein Chatbot-Wrapper.

**VERA ist eine Automated Epistemology Engine** — ein System das tut, was Wissenschaftler, Geheimdienstanalysten und Richter manuell tun: Evidenz sammeln, jede Schlussfolgerung mit einem Red Team angreifen, Überzeugungen mathematisch via Bayes updaten, und alles mit lückenloser Provenienz dokumentieren.

Das UAP-Domain ist der Stresstest. Wenn VERA in der adversarialsten Informationsumgebung der Welt funktioniert, funktioniert es überall.

**Vollständige Dokumentation auf Englisch oben. Für Fragen: GitHub Issues.**

---

<div align="center">

*Built with metacognitive precision by IrsanAI.*
*Given to the world.*

</div>
