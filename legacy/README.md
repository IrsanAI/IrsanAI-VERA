# Legacy Archive

This folder contains the prototype versions (v1.0–v1.6) developed during
the initial design session (April 14, 2026).

## Why archived, not deleted?

The evolutionary path from v1.0 → v1.6 documents real design decisions —
including the critical flaw that led to the VERA redesign: probability values
were hardcoded rather than evidence-derived.

Keeping this history is itself epistemically honest.

## Files

| File | Version | Note |
|------|---------|------|
| `AA_Investigator_v1.2.py` | v1.2 | Last stable prototype |
| `AA_Dashboard_v1.py` | v1.0 | Streamlit dashboard prototype |
| `AA_HW_Detector_v1.4.py` | v1.4 | Hardware detection module |
| `IrsanAI_HW_Report_desktop.json` | — | Windows 11 hardware profile |

## Key lesson from these prototypes

The v1.2–v1.6 runs all produced `prob_tech_coverup` values between 0.65–0.81
regardless of actual data found. The HuggingFace crawler returned 0 results
in every session after v1.1 — yet the probability held above 0.80.

This is the problem VERA solves at the architectural level:
**no value without evidence, no evidence without provenance.**
