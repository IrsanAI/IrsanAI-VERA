# Changelog

## v0.4.0 — 2026-05-03
### Added
- **Epistemic Auditor** (`core/auditor.py`) — 7 bias detectors, health scores, session audit trail
- **EpistemicAuditor** integrated into investigation cycle — monitors every Bayes update
- **Epistemic Operations Center** — complete dashboard redesign (dark mode, JetBrains Mono, Bebas Neue)
- **Belief Evolution chart** with glow effect and health score overlay
- **PatchBot** (`irsanai_patchbot.py`) — structured VERA_PATCH format for Claude↔Local bridging
- **PatchBot Status Reporter** (`irsanai_patchbot_status.py`) — LLM-ready environment snapshots
- **Preflight Scanner** (`irsanai_preflight.py`) — full system intelligence report (6 sections, deep mode)

### Changed
- Audit section added to Obsidian session notes
- Session reports include `epistemic_audit` field
- `.gitignore` protects all local toolchain files

---

## v0.3.0 — 2026-05-02
### Added
- **Streamlit Dashboard** (`dashboard/app.py`) — belief evolution, Bayes trail, evidence explorer
- **.env support** — GITHUB_TOKEN and HF_TOKEN from environment
- **Obsidian vault export** — sessions, evidence, entities as Markdown notes
- **SETUP.md** — complete setup guide with token instructions
- **Funnel query strategy** in HuggingFace agent — domain → broader → fallback

---

## v0.2.0 — 2026-05-02
### Added
- **Real Bayesian Belief Updater** — replaced all hardcoded probability values
- **Evidence dataclass** with provenance chain (source, method, timestamp, trust weight)
- **Likelihood ratio engine** — pro evidence raises belief, counter evidence lowers it
- **HuggingFace OSINT Agent** — real API integration with error handling
- **GitHub OSINT Agent** — real GitHub Search API, quality filtering by stars and recency
- **Red Team Agent** — structural counter-hypotheses + live GitHub counter-search
- **LRP v1.3 Messenger** — typed inter-agent communication with full audit log
- **Ontology Loader** — typed Python objects from YAML domain config
- **Investigation Cycle** — full orchestration: collect → update → export → save

### Removed
- All hardcoded confidence values (was the core problem of v0.1)
- Simulated news signals pretending to be real data

---

## v0.1.0 — 2026-05-01
### Added
- Project skeleton, folder structure
- Domain ontology YAML format (`ontologies/uap.yaml`)
- Legacy archive of prototype v1.0–v1.6 (preserved in `legacy/`)
- pyproject.toml, .gitignore, README, LICENSE

---

## Legacy (pre-v0.1.0)
Prototype sessions from April 14, 2026 — the first runs that exposed the core problem:
probability values were hardcoded, not evidence-derived. Preserved in `legacy/` as archaeological record.
