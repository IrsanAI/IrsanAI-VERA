# VERA // VISION
## What Becomes Possible

> This document describes features beyond the free open-source core.
> Every item here is an open invitation — to community builders, investors, or anyone who sees the potential.
> The core stays free. What you build on top is yours.

---

## The Experience That Doesn't Exist Yet

Imagine this:

A user opens a browser. One sentence greets them — not a headline, not a slogan. A question. The kind you've always wanted answered but never knew how to ask.

An input field. Elegant. Minimal. Alive.

As the user types, the typography transforms in near-realtime — an RL agent reads the semantic context and shifts the visual language to match: technical queries render in monospace precision, philosophical questions in flowing humanist type, conspiracy territory in sharp high-contrast. The font *becomes* the thought.

A ghost word appears ahead of the cursor. Semi-transparent. Predictive. Like Linux tab-completion but trained on the user's own reasoning patterns.

The user submits.

What follows is not a loading spinner.

What follows is VERA waking up.

---

## The Five Layers of the Vision

### Layer 1 — Adaptive Interface
**RL-driven typography** that transforms based on semantic context. Tab-completion trained per user. Auth via OAuth (GitHub, Google, Microsoft). Progressive disclosure — the interface reveals complexity only as the user needs it.

**Technical path:** React frontend + Python RL microservice + WebSocket real-time updates. Zero cost locally, marginal cost hosted.

### Layer 2 — The Journey (Immersive Investigation UX)
While VERA's agents work, the user is not passive. They are pulled into the process:

- Phase 1: The question crystallizes visually
- Phase 2: Sources appear as a growing constellation
- Phase 3: The Red Team attack is visible — nodes shake, evidence destabilizes
- Phase 4: Bayesian updates pulse as probability shifts
- Phase 5: The knowledge graph assembles around the user in 3D

A second RL agent learns per-user how deep to go, how fast to reveal, which visual metaphors resonate. One user wants raw data. Another wants cinematic narrative. The system learns.

**Technical path:** Three.js / WebGL frontend, per-user RL model (small, local-trainable), WebSocket streaming from FastAPI backend.

### Layer 3 — Global Unique Keys
Every completed VERA investigation receives a cryptographic unique key. Immutable. Timestamped. Verifiable.

This key represents: *"At this moment in time, with this evidence, this was the most epistemically honest answer available."*

Users can share keys. Compare keys. Challenge each other's keys with new evidence.

**Technical path:** UUID4 + SHA256 hash of session data. Storage: Supabase free tier or self-hosted PostgreSQL.

### Layer 4 — Distributed Learning
Every completed investigation (with user consent) enriches the global ontology. Patterns across thousands of users become visible. Which queries find real signal? Which sources consistently produce high-trust evidence? Which Red Team strategies are most effective?

The system gets smarter with every user. Not by training on content — by learning which *epistemic strategies* work.

**Technical path:** Federated learning patterns. Optional anonymous contribution. GDPR-compliant by design.

### Layer 5 — The Metacognitive Twin
The Autopilot (`core/autopilot.py` — in development) becomes a full Reflexive Epistemic Twin: a meta-agent that doesn't just select strategies but monitors the quality of its own reasoning, proposes ontology improvements, and flags when the Three Musketeers are out of resonance.

This is the part that makes VERA genuinely self-improving — not in the dangerous "rewriting its own goals" sense, but in the "getting better at finding truth" sense.

---

## Domain Expansion Roadmap

| Domain | Ontology File | Community Status |
|--------|--------------|-----------------|
| UAP / Disclosure | `uap.yaml` | ✅ Proof of concept |
| Medical Research Fraud | `oncology.yaml` | 📋 Community invitation |
| Financial Crime | `finance.yaml` | 📋 Community invitation |
| Climate Data Synthesis | `climate.yaml` | 📋 Community invitation |
| Scientific Misconduct | `academic_fraud.yaml` | 📋 Community invitation |
| Legal Due Diligence | `legal.yaml` | 📋 Community invitation |
| Cybersecurity Threat Intel | `cybersec.yaml` | 📋 Community invitation |

**To add a domain:** Fork the repo, create an ontology YAML following the schema in `ontologies/uap.yaml`, submit a PR. That's it.

---

## What Would Cost Money (Transparency)

| Feature | Why it costs | Estimated cost |
|---------|-------------|----------------|
| Global hosted instance | Server + storage | ~$20-50/month |
| GPU for NLP models | sentence-transformers inference | ~$0-10/month (Colab/HF free tier) |
| Auth providers | OAuth setup | $0 (free tiers) |
| Database for global keys | Supabase | $0 (free tier up to 500MB) |
| CDN for 3D frontend | Vercel/Netlify | $0 (free tier) |

**Conclusion:** A basic hosted version of the full vision is achievable for under $50/month. A serious production deployment for a team is ~$200-500/month.

The open-source self-hosted version costs €0.00. Forever.

---

## For Investors / Builders

If you see what this could be and want to build it:

1. Fork the repo
2. Build one layer of the vision
3. Open a PR or open an Issue describing what you've built
4. Keep it MIT — the core stays free

If you want to commercialize: the license allows it. Build a SaaS on top. Sell enterprise ontologies. Offer hosted investigations. The only ask: give back improvements to the core.

---

*"The world builds on what someone once gave away."*

*— IrsanAI, 2026*
