# IrsanAI-VERA — Roadmap

## v0.1.0 — Foundation (current)
- [x] Project skeleton & folder structure
- [x] Domain ontology YAML format (UAP example)
- [x] Bayesian Belief Updater with provenance chain
- [x] Evidence dataclass with likelihood ratios
- [x] Obsidian vault exporter
- [x] pyproject.toml, .gitignore, README
- [ ] Ontology loader (reads YAML → config)
- [ ] LRP v1.3 inter-agent message format

## v0.2.0 — Real Data
- [ ] HuggingFace agent (semantic search, not keyword)
- [ ] GitHub OSINT agent (real API, repo quality filtering)
- [ ] RSS news crawler (trust-weighted sources from ontology)
- [ ] ChromaDB integration (cross-session vector memory)
- [ ] First real investigation cycle with honest probabilities

## v0.3.0 — Adversarial Layer
- [ ] Red Team Agent (counter-evidence seeker)
- [ ] Adversarial synthesis: Pro vs Counter → Bayesian verdict
- [ ] Claim-Evidence dependency graph (NetworkX)
- [ ] Obsidian entity notes auto-generated from graph

## v0.4.0 — Intelligence Layer
- [ ] Sentence-transformer NLP signal processor
- [ ] Cross-session memory (ChromaDB) with similarity search
- [ ] Autopilot: RL strategy selector based on historical signal yield
- [ ] LRP v1.3 inter-agent communication protocol

## v0.5.0 — Interface
- [ ] FastAPI backend (replaces Streamlit for production)
- [ ] Real-time WebSocket updates to dashboard
- [ ] Streamlit dashboard (current reports + belief timeline)
- [ ] CLI improvements: `vera run`, `vera status`, `vera export`

## v1.0.0 — Production
- [ ] Docker container + docker-compose
- [ ] Scheduled runs (system service or cron)
- [ ] Multi-domain support (run multiple ontologies)
- [ ] Full documentation
- [ ] Unit tests for Bayesian core

## Domain Ontologies Planned
- `uap.yaml` — UAP/Disclosure (proof-of-concept)
- `pharma_fraud.yaml` — Drug efficacy misrepresentation
- `financial_crime.yaml` — Structured financial anomaly detection
- `climate_data.yaml` — Multi-source climate sensor synthesis
- `academic_fraud.yaml` — Scientific misconduct pattern detection

## Legacy
The `legacy/` folder contains prototype versions v1.0–v1.6 from the initial
development session. These are archived for historical context.
Their core limitation: probability values were hardcoded, not evidence-derived.
VERA fixes this at the architectural level.
