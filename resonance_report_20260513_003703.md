# IrsanAI-VERA — Resonance Reporter
**Generated**: 2026-05-13 00:37:02  |  **Target LLM**: CLAUDE
**Repo**: https://github.com/IrsanAI/IrsanAI-VERA
**System Health**: 🟢 HEALTHY

> DSGVO-compliant. No personal data. No tokens. No PII.
> Path anonymized. Session IDs truncated.

---

## ⬡ IST / SOLL State

| Metric | Value |
|--------|-------|
| Canonical modules expected | `23` |
| Modules present (IST) | `23` |
| Modules missing (SOLL gap) | `0` |
| Planned future modules | `6` |
| Critical issues | `0` |
| High issues | `0` |
| Medium issues | `0` |
| Git branch | `main` |
| Last commit | `c4dab47` — feat: v3 dashboard improvements + graph integration |
| Working tree | `Clean` |
| Unpushed | `False` |

## ✅ No Deviations Detected

IST matches SOLL. System integrity confirmed.

## 📊 Dashboard State (Latest Session)

| KPI | Value |
|-----|-------|
| Domain | `UAP Disclosure` |
| Current Belief | `32.0%` |
| Prior | `10.0%` |
| Net Shift | `+22.0%` |
| Pro Evidence | `17` |
| Counter Evidence | `4` |
| Verdict | `Weak signal — monitoring` |
| Health Score | N/A |
| Audit Warnings | `15` |
| LRP Messages | `35` |
| Duration | `31.4s` |
| Total Bayes Updates | `203` |
| Mean Likelihood Ratio | `0.9523` |

**Audit Warning Types:**
- `CONFIRMATION_DRIFT` ×15

## 📈 Belief Trend (Last 5 Sessions)

| Timestamp | Belief | Pro/Counter | Verdict | Health |
|-----------|--------|-------------|---------|--------|
| `2026-05-13T00:00:11` | `32.0%` | `17✅/4❌` | Weak signal — monitoring | — |
| `2026-05-11T23:29:27` | `31.1%` | `17✅/4❌` | Weak signal — monitoring | — |
| `2026-05-10T14:52:54` | `29.9%` | `17✅/4❌` | Weak signal — monitoring | — |
| `2026-05-10T13:57:58` | `29.9%` | `17✅/4❌` | Weak signal — monitoring | — |
| `2026-05-09T14:24:38` | `27.6%` | `17✅/4❌` | Weak signal — monitoring | — |

## 🔧 PatchBot History (Last 5)

| Session | Patches | Result | Files |
|---------|---------|--------|-------|
| `20260512_235102` | 1 | ✅ 1/1 | `core/investigation_cycle.py` |
| `20260508_003727` | 1 | ✅ 1/1 | `.gitignore` |
| `20260508_003425` | 1 | ⚠️ 0/1 (1 failed) | — |
| `20260507_070637` | 1 | ✅ 1/1 | `agents/osint_github.py` |
| `20260507_064734` | 1 | ✅ 1/1 | `dashboard/app.py` |

## ✅ Validation Checklist (for LLM)

After applying any patches, verify:

- [ ] `python vera.py --ontology ontologies/uap.yaml --no-obsidian` runs without error
- [ ] Belief updates from real evidence (not hardcoded)
- [ ] Red Team produces counter-evidence (`supports_hypothesis=False`)
- [ ] Epistemic Auditor produces health score
- [ ] Dashboard loads: `streamlit run dashboard/app.py`
- [ ] Run Resonance Reporter again: `python irsanai_resonance_reporter.py`
- [ ] All CRITICAL/HIGH issues resolved

---

*IrsanAI-VERA Resonance Reporter v1.0*
*Canonical reference: https://github.com/IrsanAI/IrsanAI-VERA*
*Generated: 2026-05-13 00:37:02*