# IrsanAI-VERA — Resonance Reporter
**Generated**: 2026-05-28 11:14:11  |  **Target LLM**: CLAUDE
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
| Last commit | `372c4ff` — Fix f-string syntax errors locally |
| Working tree | `Uncommitted changes` |
| Unpushed | `True` |

## ✅ No Deviations Detected

IST matches SOLL. System integrity confirmed.

## 📊 Dashboard State (Latest Session)

| KPI | Value |
|-----|-------|
| Domain | `UAP Disclosure` |
| Current Belief | `96.0%` |
| Prior | `10.0%` |
| Net Shift | `+86.1%` |
| Pro Evidence | `16` |
| Counter Evidence | `4` |
| Verdict | `Conclusive — peer review recommended` |
| Health Score | N/A |
| Audit Warnings | `9` |
| LRP Messages | `33` |
| Duration | `42.6s` |
| Total Bayes Updates | `251` |
| Mean Likelihood Ratio | `1.0217` |

**Audit Warning Types:**
- `CONFIRMATION_DRIFT` ×9

## 📈 Belief Trend (Last 5 Sessions)

| Timestamp | Belief | Pro/Counter | Verdict | Health |
|-----------|--------|-------------|---------|--------|
| `2026-05-28T00:15:38` | `96.0%` | `16✅/4❌` | Conclusive — peer review recommended | — |
| `2026-05-28T00:07:45` | `10.0%` | `0✅/0❌` | No significant evidence | 🟡 0.65 |
| `2026-05-25T23:59:44` | `10.0%` | `0✅/0❌` | No significant evidence | 🔴 0.35 |
| `2026-05-17T10:40:52` | `10.0%` | `0✅/0❌` | No significant evidence | 🔴 0.35 |
| `2026-05-16T23:43:06` | `87.7%` | `7✅/0❌` | Conclusive — peer review recommended | — |

## 🔧 PatchBot History (Last 5)

| Session | Patches | Result | Files |
|---------|---------|--------|-------|
| `20260515_025601` | 1 | ✅ 1/1 | `dashboard/app.py` |
| `20260515_023630` | 4 | ⚠️ 3/4 (1 failed) | `dashboard/app.py` |
| `20260514_122630` | 1 | ✅ 1/1 | `.gitignore` |
| `20260512_235102` | 1 | ✅ 1/1 | `core/investigation_cycle.py` |
| `20260508_003727` | 1 | ✅ 1/1 | `.gitignore` |

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
*Generated: 2026-05-28 11:14:11*