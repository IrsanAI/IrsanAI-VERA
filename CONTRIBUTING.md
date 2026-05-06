# Contributing to IrsanAI-VERA

VERA is built on a simple principle: **truth is harder to find than we think, and the tools we use to find it matter.**

If you believe that — welcome.

---

## What We Need

### 🔧 Module Builders
These modules are planned but not yet built. Each one is an open invitation:

| Module | Path | Complexity | Impact |
|--------|------|-----------|--------|
| Autopilot / Resonance Controller | `core/autopilot.py` | High | 🔴 Critical |
| ChromaDB Cross-Session Memory | `core/memory/chromadb_store.py` | Medium | 🔴 Critical |
| NLP Semantic Signal Agent | `agents/nlp_signal.py` | Medium | 🟠 High |
| NetworkX Knowledge Graph | `core/graph/knowledge_graph.py` | Medium | 🟠 High |
| FastAPI Backend | `api/server.py` | Medium | 🟡 Medium |
| Docker Config | `Dockerfile` | Low | 🟡 Medium |
| HuggingFace Spaces Deploy | `spaces/` | Low | 🟢 Visibility |

### 🌍 Domain Ontologies
Create a new YAML in `ontologies/` following the schema in `ontologies/uap.yaml`. Every new domain multiplies VERA's impact.

**Most wanted:**
- `ontologies/oncology.yaml` — medical research fraud
- `ontologies/finance.yaml` — financial crime patterns
- `ontologies/climate.yaml` — climate data synthesis
- `ontologies/cybersec.yaml` — threat intelligence

### 📖 Documentation
- Translations (the community is global)
- Tutorial notebooks
- Case studies using VERA on real questions
- Academic paper contributions

### 🧪 Testing
- Unit tests for the Bayesian core
- Integration tests for agent pipelines
- Edge case ontologies

---

## How to Contribute

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/IrsanAI-VERA.git
cd IrsanAI-VERA

# 2. Create a branch
git checkout -b feat/your-feature-name

# 3. Install dependencies
pip install requests pyyaml psutil streamlit plotly pandas networkx

# 4. Make your changes

# 5. Test
python vera.py --ontology ontologies/uap.yaml --no-obsidian

# 6. Commit with clear message
git commit -m "feat: add chromadb cross-session memory"

# 7. Push and open PR
git push origin feat/your-feature-name
```

---

## Design Principles (Please Read)

**Epistemic honesty first.** No probability value without real evidence. No shortcut that produces plausible-looking fake output.

**Provenance always.** Every piece of evidence needs: source URL, retrieval method, timestamp, trust weight.

**Red Team is not optional.** If you add a new agent that finds pro-evidence, you must also consider how the Red Team challenges it.

**Domain agnosticism.** New features should work via ontology configuration, not hardcoded domain logic.

**Minimal dependencies.** Before adding a new package, ask: is this necessary?

---

## Code Style

- Python 3.11+
- Type hints everywhere
- Docstrings for all public classes and methods
- No hardcoded values — everything configurable via ontology or environment

---

## Questions?

Open an Issue. We read everything.

---

*"Build first. The world needs this more than it needs another closed system."*
