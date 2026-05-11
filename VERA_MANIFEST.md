# VERA_MANIFEST.md
## The Immovable Foundation of IrsanAI-VERA

> This document defines what VERA *is*, what it *must never become*,
> and what milestones must be reached before the next phase begins.
>
> **It is validated automatically on every push via GitHub Actions.**
> A failing manifest check blocks merges to `main`.

---

## 1. Core Identity (Never Changes)

VERA is an **Automated Epistemology Engine**.

It is NOT:
- A search engine
- A chatbot wrapper
- An OSINT scraper that produces plausible-looking output
- A system that generates confidence values without evidence

It IS:
- A system where every probability traces back to real, documented evidence
- A system that actively attacks its own conclusions (Red Team)
- A system that monitors its own reasoning for bias (Epistemic Auditor)
- A system that works the same way regardless of domain (Domain Agnosticism)

---

## 2. The Three Golden Protocols (Inviolable)

These are not configurable. They are architectural constants.

**Lex Bayesian:** No belief value may reach exactly 1.0 or 0.0.
Absolute certainty is mathematically forbidden.

**Lex Adversaria:** The Red Team Agent is mandatory.
No investigation cycle may complete without adversarial counter-evidence being sought.

**Lex Proventia:** Any evidence without a verifiable provenance chain
(source URL + retrieval method + timestamp) receives trust weight = 0.

---

## 3. The Three Musketeers (Core Architecture)

| Unit | Module | Status |
|------|--------|--------|
| ⚖️ Bayes | `core/bayesian/updater.py` | ✅ Implemented |
| ⚔️ Adversary | `agents/red_team.py` | ✅ Implemented |
| 🔗 Provenance | `core/bayesian/evidence.py` | ✅ Implemented |
| 🎯 Conductor | `core/autopilot.py` | 📋 v0.5.0 |

**Resonance Rule:** The Conductor (Autopilot) must enforce that no two units
can form a coalition against the third. Two against one = negative reward.
Only resonance of all three produces valid knowledge.

---

## 4. Current System State (v0.4.0)

### Implemented ✅
- Bayesian Belief Updater with full provenance chain
- Evidence dataclass with likelihood ratios, age decay, corroboration bonus
- HuggingFace OSINT Agent (real API, funnel strategy)
- GitHub OSINT Agent (real Search API, quality filtering)
- Red Team Agent (structural + live adversarial search)
- LRP v1.3 inter-agent communication protocol
- Epistemic Auditor (7 bias detectors, health scores)
- Ontology Loader (domain-agnostic YAML config)
- Investigation Cycle (full orchestration)
- Obsidian Vault Exporter (linked knowledge graph)
- Epistemic Operations Center Dashboard
- PatchBot (LLM↔Local bridge)
- Preflight Scanner + Resonance Reporter

### First Validated Run
- Domain: UAP Disclosure
- Evidence found: 17 pro / 4 counter
- Belief: 10.0% → 29.9%
- Verdict: "Weak signal — monitoring"
- Auditor health: 🔴 0.000 (expected — confirmation drift from single-source sweep)

---

## 5. Phase Gates

### Gate A → B: Research (ongoing)
*Condition:* System produces epistemically honest outputs with real evidence.
**STATUS: ✅ PASSED** — v0.4.0 operational, 17 real GitHub repos, Bayesian updates verified.

### Gate B → C: Stability
*Condition:* All of the following must be true:
- [ ] `core/autopilot.py` implemented and tested (Resonance Controller)
- [ ] ChromaDB cross-session memory operational
- [ ] NLP semantic scoring replacing keyword matching
- [ ] Health score consistently ≥ 0.7 across 10 investigation cycles
- [ ] Zero CRITICAL issues in Resonance Reporter
- [ ] `requirements.txt` complete, venv reproducible
- [ ] All unit tests passing (`pytest tests/`)

**STATUS: 🔨 In progress — v0.5.0**

### Gate C → D: World
*Condition:* All of the following must be true:
- [ ] Gate B fully passed
- [ ] HuggingFace Spaces demo live (free, accessible globally)
- [ ] Docker self-hosting works (`docker-compose up`)
- [ ] CONTRIBUTING.md has produced at least 1 external PR or Issue
- [ ] GitHub Discussions active
- [ ] At least 1 domain ontology beyond UAP contributed by community

**STATUS: 📋 Planned**

### Gate D: Sustained Operation
*Condition:* The project sustains itself without the original creator's daily involvement.
Community maintains, extends, and governs VERA independently.

**This is the ultimate goal. Everything before it is preparation.**

---

## 6. What Must Never Happen

- Hardcoded probability values (the original sin of the v0.1 prototype)
- Evidence accepted without source URL and timestamp
- Red Team Agent disabled or bypassed
- Belief values clamped to 1.0 or 0.0
- Domain logic embedded in core code (always via ontology YAML)
- Personal data committed to the repository
- The VERA_MANIFEST.md itself modified without community review

---

## 7. Validation

This manifest is automatically checked on every push by `.github/workflows/manifest_check.yml`.

Manual validation:
```bash
python scripts/validate_manifest.py
```

If validation fails, the push is blocked until the issue is resolved.

---

*IrsanAI-VERA MANIFEST v1.0 — May 2026*
*This document belongs to the community. It can only be changed by the community.*
