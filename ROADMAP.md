# IrsanAI-VERA — Roadmap

## v0.4.0 — Current Release ✅
> All items below are **complete and operational** as of May 2026.

- [x] Project skeleton & modular folder structure
- [x] Domain ontology YAML format (`ontologies/uap.yaml`) with entities, semantic seeds, Red Team config
- [x] Bayesian Belief Updater — real Bayes theorem, no hardcoded values
- [x] Evidence dataclass with full provenance chain (source, method, timestamp, trust weight)
- [x] Likelihood ratio engine — pro evidence raises belief, counter evidence lowers it
- [x] HuggingFace OSINT Agent — real API, funnel query strategy
- [x] GitHub OSINT Agent — real GitHub Search API, quality filtering
- [x] Red Team Agent — structural counter-hypotheses + live adversarial search
- [x] LRP v1.3 Messenger — typed inter-agent communication, full audit log
- [x] Ontology Loader — typed Python objects from YAML domain config
- [x] Investigation Cycle — full orchestration: collect → update → export → save
- [x] Epistemic Auditor — 7 bias detectors, health scores, session audit trail
- [x] Obsidian Vault Exporter — sessions, evidence, entities as linked Markdown
- [x] Epistemic Operations Center Dashboard (dark mode, real-time belief curves)
- [x] PatchBot — structured VERA_PATCH format for LLM↔Local bridging
- [x] Preflight Scanner — full system intelligence report for LLM context
- [x] Resonance Reporter — IST/SOLL validator, auto-repair proposals
- [x] VERA_MANIFEST.md + GitHub Actions validation gate
- [x] venv + requirements.txt + clean repo structure
- [x] README as manifest, VISION.md, CONTRIBUTING.md, DONATE.md, CHANGELOG.md

**First real run results:** 17 GitHub repos found, Belief 29.9%, Verdict: "Weak signal — monitoring"

---

## v0.5.0 — Memory & Intelligence Layer 📋
> Next milestone. Community contributions welcome — see CONTRIBUTING.md

- [ ] `core/autopilot.py` — Resonance Controller (Three Musketeers balance)
- [ ] `core/memory/chromadb_store.py` — Cross-session vector memory (ChromaDB)
- [ ] `agents/nlp_signal.py` — Semantic NLP scoring via sentence-transformers
- [ ] `core/graph/knowledge_graph.py` — NetworkX entity graph, cross-session links
- [ ] Fix confirmation drift: interleave pro/counter evidence in update order
- [ ] Extended ontology v2 — falsification criteria, causal links, update triggers per entity

---

## v0.6.0 — API & Deployment Layer 📋

- [ ] `api/server.py` — FastAPI backend (replaces Streamlit for production)
- [ ] Real-time WebSocket updates to dashboard
- [ ] `Dockerfile` + `docker-compose.yml` — one-command self-hosting
- [ ] HuggingFace Spaces deployment (free global demo)
- [ ] Scheduled investigation runs (cron / system service)

---

## v1.0.0 — Production 📋

- [ ] Multi-domain parallel investigations
- [ ] Full unit + integration test suite
- [ ] Complete API documentation
- [ ] GitHub Discussions active + community governance
- [ ] Performance benchmarks for Bayesian core

---

## Domain Ontologies

| File | Domain | Status |
|------|--------|--------|
| `ontologies/uap.yaml` | UAP / Government Disclosure | ✅ Proof of concept |
| `ontologies/oncology.yaml` | Medical research fraud | 📋 Community invitation |
| `ontologies/finance.yaml` | Financial crime patterns | 📋 Community invitation |
| `ontologies/climate.yaml` | Climate data synthesis | 📋 Community invitation |
| `ontologies/academic_fraud.yaml` | Scientific misconduct | 📋 Community invitation |
| `ontologies/legal.yaml` | Legal due diligence | 📋 Community invitation |

---

## Legacy

The `legacy/` folder contains prototype versions v1.0–v1.6 (April 14, 2026).

Core limitation of all legacy versions: probability values were hardcoded, not evidence-derived.
VERA v0.2.0+ fixes this at the architectural level — no value without real evidence.

---

*For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)*
*For the full vision of what can be built on top, see [VISION.md](VISION.md)*
