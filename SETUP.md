# IrsanAI-VERA — Setup Guide

## 1. Requirements

- Python 3.11+
- Git
- (Optional) GitHub Personal Access Token — strongly recommended
- (Optional) Obsidian — for knowledge graph visualization

---

## 2. Install Dependencies

```powershell
# In your PyCharm terminal or PowerShell:
pip install requests pyyaml psutil streamlit plotly pandas
```

For Obsidian export (optional but recommended):
```powershell
pip install networkx
```

---

## 3. Set Up Your Tokens (.env)

This is the most important step. Without a GitHub token, the GitHub agent
hits rate limits immediately and finds nothing.

```powershell
# Copy the template
copy .env.example .env
```

Then open `.env` in PyCharm and fill in:

```
GITHUB_TOKEN=ghp_your_token_here
```

**How to get a GitHub token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `IrsanAI-VERA`
4. Scopes: check `public_repo` only (read-only)
5. Copy the token → paste into `.env`

**How to get a HuggingFace token (optional):**
1. Go to https://huggingface.co/settings/tokens
2. New token → Role: Read
3. Copy → paste as `HF_TOKEN=` in `.env`

---

## 4. Set Up Obsidian (Optional but Recommended)

1. Download Obsidian from https://obsidian.md
2. Open Obsidian → "Open folder as vault"
3. Point it to your VERA project's `vault/` folder
   (or set a custom path in `.env`: `OBSIDIAN_VAULT_PATH=C:/your/vault`)
4. After each VERA run, refresh Obsidian → the knowledge graph updates

Recommended Obsidian plugins:
- **Dataview** — query evidence as a database
- **Graph Analysis** — see entity centrality
- **Templater** — auto-format new evidence notes

---

## 5. Run VERA

```powershell
# Basic run (with Obsidian export)
python vera.py --ontology ontologies/uap.yaml

# Without Obsidian (faster, no vault write)
python vera.py --ontology ontologies/uap.yaml --no-obsidian

# Multiple cycles (builds belief over time)
python vera.py --ontology ontologies/uap.yaml --cycles 5

# Open dashboard
streamlit run dashboard/app.py
```

---

## 6. Understand the Output

```
data/
├── vera_YYYYMMDD_HHMMSS_XXXX_report.json   ← Full session report
├── vera_YYYYMMDD_HHMMSS_XXXX_lrp_bus.jsonl ← Agent messages (LRP v1.3)
└── belief_updates.jsonl                     ← Every Bayes update step

vault/
├── _index.md          ← Investigation overview
├── sessions/          ← One note per run
├── evidence/          ← One note per piece of evidence
└── entities/          ← Tracked entities (AARO, Pentagon, etc.)
```

**Key principle:** The `belief_updates.jsonl` file is the ground truth.
Every probability change traces back to a specific evidence piece.
If the system finds nothing → belief stays at prior or drops (Red Team).
There are no hardcoded values.

---

## 7. Add a New Domain

Copy and edit the ontology:
```powershell
copy ontologies\uap.yaml ontologies\my_domain.yaml
```

Change these fields in the YAML:
- `meta.domain` — domain name
- `bayesian.prior_*` — starting probabilities (keep these LOW)
- `entities` — relevant organizations/sources for your domain
- `semantic_seeds` — key phrases to look for
- `sources.github_queries` — what to search on GitHub
- `red_team.counter_hypotheses` — skeptical positions

Then run:
```powershell
python vera.py --ontology ontologies/my_domain.yaml
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| GitHub agent finds nothing | Add GITHUB_TOKEN to .env |
| HF agent finds nothing | Add HF_TOKEN to .env |
| Obsidian vault not updating | Check OBSIDIAN_VAULT_PATH in .env |
| `pip install -e` fails | Use `pip install requests pyyaml psutil` directly |
| Belief stays at prior | Normal — not enough evidence found yet |
| Belief drops below prior | Normal — Red Team counter-evidence is working |
