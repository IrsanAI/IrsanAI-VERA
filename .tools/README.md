# IrsanAI Local Toolchain

This folder contains local-only tools that bridge Claude (online LLM) and your local environment.

**Never committed to GitHub** — protected by `.gitignore`.

## Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `irsanai_preflight.py` | Full system scan for Claude | `python .tools/irsanai_preflight.py` |
| `irsanai_patchbot.py` | Apply VERA_PATCH instructions | `python .tools/irsanai_patchbot.py patch.txt` |
| `irsanai_patchbot_status.py` | LLM-ready status snapshot | `python .tools/irsanai_patchbot_status.py` |
| `irsanai_resonance_reporter.py` | IST/SOLL validator | `python .tools/irsanai_resonance_reporter.py` |

## Subfolders

- `patches/` — All VERA_PATCH files
- `reports/` — Generated preflight and resonance reports
