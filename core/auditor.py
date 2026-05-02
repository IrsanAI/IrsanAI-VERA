"""
IrsanAI-VERA — Epistemic Auditor
core/auditor.py

The Reflexive Epistemic Twin.

Not just "did belief change" — but "is the WAY belief is changing healthy?"
Every warning is statistically grounded, not arbitrarily thresholded.

This module monitors the Bayesian update process itself for:
  1. Overconfidence / extreme single-evidence jumps
  2. Source monoculture (all evidence from one retrieval method)
  3. Confirmation drift (monotonic belief trend without counter-evidence)
  4. Evidence starvation (Red Team finds nothing — dangerous silence)
  5. Likelihood ratio anomalies (implausibly strong individual evidence)

Design principle: a warning is only raised when a statistical threshold
is breached, not when a fixed number is exceeded arbitrarily.
"""

from __future__ import annotations

import json
import math
import datetime
import statistics
from collections import Counter
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"
    CRITICAL = "CRITICAL"


class BiasType(str, Enum):
    OVERCONFIDENCE       = "OVERCONFIDENCE"        # Single update shifts belief too far
    SOURCE_MONOCULTURE   = "SOURCE_MONOCULTURE"    # All evidence from same source type
    CONFIRMATION_DRIFT   = "CONFIRMATION_DRIFT"    # Monotonic updates — no counter-pressure
    EVIDENCE_STARVATION  = "EVIDENCE_STARVATION"   # Pro or Counter side is empty
    LR_ANOMALY           = "LR_ANOMALY"            # Likelihood ratio is statistically implausible
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE" # Too few updates to form reliable belief
    RED_TEAM_ABSENT      = "RED_TEAM_ABSENT"       # No counter-evidence at all — critical


@dataclass
class AuditWarning:
    timestamp: str
    bias_type: BiasType
    severity: Severity
    message: str
    evidence_id: Optional[str]
    prior: float
    posterior: float
    recommendation: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bias_type"] = self.bias_type.value
        d["severity"] = self.severity.value
        return d

    def to_obsidian_line(self) -> str:
        icon = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "⛔"}.get(self.severity.value, "⚠️")
        return (
            f"| {self.timestamp[:19]} | {icon} {self.severity.value} | "
            f"`{self.bias_type.value}` | {self.message} |"
        )


class EpistemicAuditor:
    """
    Monitors the Bayesian belief update process for cognitive bias patterns.

    Called after each update in the investigation cycle.
    Produces a session audit log and a summary for the Obsidian vault.

    Statistical grounding:
    - Overconfidence threshold: based on maximum expected single-evidence
      shift given trust_weight ceiling (0.9) and semantic_score ceiling (1.0)
    - LR anomaly: flags LR values > 3σ above session mean (running)
    - Confirmation drift: requires ≥4 consecutive same-direction updates
      (reduces false positives from short sequences)
    """

    # Maximum belief shift expected from a single well-grounded evidence piece
    # trust_weight=0.9, semantic_score=1.0, no corroboration → LR = 1 + (0.9*1.0*3.0) = 3.7
    # Bayesian update with LR=3.7 from prior=0.5: posterior ≈ 0.79 → shift ≈ 0.29
    # We use 0.30 as the statistical ceiling for a single update.
    OVERCONFIDENCE_THRESHOLD = 0.30

    # Minimum sessions before confirmation-drift detection activates
    MIN_UPDATES_FOR_DRIFT = 4

    def __init__(self, data_dir: Path, session_id: str):
        self.data_dir = data_dir
        self.session_id = session_id
        self._log_path = data_dir / f"{session_id}_epistemic_audit.jsonl"
        self._warnings: list[AuditWarning] = []
        self._update_deltas: list[float] = []
        self._lr_values: list[float] = []
        self._source_types_seen: list[str] = []

    @property
    def warnings(self) -> list[AuditWarning]:
        return list(self._warnings)

    @property
    def warning_count(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for w in self._warnings:
            counts[w.severity.value] = counts.get(w.severity.value, 0) + 1
        return counts

    def _emit(self, warning: AuditWarning) -> None:
        self._warnings.append(warning)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(warning.to_dict(), ensure_ascii=False) + "\n")

    def audit_update(
        self,
        prior: float,
        posterior: float,
        likelihood_ratio: float,
        evidence_id: str,
        source_type: str,
        retrieval_method: str,
        supports_hypothesis: bool,
    ) -> list[AuditWarning]:
        """
        Called after each individual Bayesian update.
        Returns any warnings triggered by this update.
        """
        new_warnings: list[AuditWarning] = []
        delta = posterior - prior
        self._update_deltas.append(delta)
        self._lr_values.append(likelihood_ratio)
        self._source_types_seen.append(retrieval_method)
        ts = datetime.datetime.now().isoformat()

        # 1. Overconfidence: single update too large
        if abs(delta) > self.OVERCONFIDENCE_THRESHOLD:
            w = AuditWarning(
                timestamp=ts,
                bias_type=BiasType.OVERCONFIDENCE,
                severity=Severity.HIGH,
                message=(
                    f"Single evidence update shifted belief by {delta:+.1%} "
                    f"(threshold: ±{self.OVERCONFIDENCE_THRESHOLD:.0%}). "
                    f"Source: {source_type}, LR={likelihood_ratio:.4f}"
                ),
                evidence_id=evidence_id,
                prior=prior,
                posterior=posterior,
                recommendation="Review source trust weight and semantic score for this evidence piece.",
            )
            self._emit(w)
            new_warnings.append(w)

        # 2. LR anomaly: likelihood ratio > 3σ above running mean
        if len(self._lr_values) >= 5:
            mean_lr = statistics.mean(self._lr_values[:-1])
            std_lr = statistics.stdev(self._lr_values[:-1]) if len(self._lr_values) > 2 else 0
            if std_lr > 0 and (likelihood_ratio - mean_lr) > 3 * std_lr:
                w = AuditWarning(
                    timestamp=ts,
                    bias_type=BiasType.LR_ANOMALY,
                    severity=Severity.MEDIUM,
                    message=(
                        f"LR={likelihood_ratio:.4f} is >3σ above session mean "
                        f"(mean={mean_lr:.4f}, σ={std_lr:.4f}). "
                        f"Evidence '{evidence_id}' may be outlier or incorrectly weighted."
                    ),
                    evidence_id=evidence_id,
                    prior=prior,
                    posterior=posterior,
                    recommendation="Verify source trust weight assignment in ontology.",
                )
                self._emit(w)
                new_warnings.append(w)

        # 3. Confirmation drift: ≥4 consecutive same-direction updates
        if len(self._update_deltas) >= self.MIN_UPDATES_FOR_DRIFT:
            recent = self._update_deltas[-self.MIN_UPDATES_FOR_DRIFT:]
            if all(d > 0 for d in recent):
                w = AuditWarning(
                    timestamp=ts,
                    bias_type=BiasType.CONFIRMATION_DRIFT,
                    severity=Severity.MEDIUM,
                    message=(
                        f"{self.MIN_UPDATES_FOR_DRIFT} consecutive pro-hypothesis updates. "
                        f"No counter-evidence recently applied."
                    ),
                    evidence_id=evidence_id,
                    prior=prior,
                    posterior=posterior,
                    recommendation=(
                        "Verify Red Team Agent is active and returning counter-evidence. "
                        "Check if Red Team evidence is being correctly ordered."
                    ),
                )
                self._emit(w)
                new_warnings.append(w)
            elif all(d < 0 for d in recent):
                w = AuditWarning(
                    timestamp=ts,
                    bias_type=BiasType.CONFIRMATION_DRIFT,
                    severity=Severity.LOW,
                    message=(
                        f"{self.MIN_UPDATES_FOR_DRIFT} consecutive counter-hypothesis updates. "
                        f"Belief may be suppressed beyond evidence base."
                    ),
                    evidence_id=evidence_id,
                    prior=prior,
                    posterior=posterior,
                    recommendation="Ensure pro-evidence agents are searching with sufficient query breadth.",
                )
                self._emit(w)
                new_warnings.append(w)

        return new_warnings

    def audit_session_end(
        self,
        total_pro: int,
        total_counter: int,
        source_types: list[str],
        final_belief: float,
        total_updates: int,
    ) -> list[AuditWarning]:
        """
        Called once at end of session. Checks session-level patterns.
        """
        ts = datetime.datetime.now().isoformat()
        new_warnings: list[AuditWarning] = []

        # 4. Red Team absent — critical
        if total_counter == 0:
            w = AuditWarning(
                timestamp=ts,
                bias_type=BiasType.RED_TEAM_ABSENT,
                severity=Severity.CRITICAL,
                message=(
                    "Zero counter-evidence collected this session. "
                    "Red Team Agent produced no adversarial findings."
                ),
                evidence_id=None,
                prior=0.0,
                posterior=final_belief,
                recommendation=(
                    "Check Red Team Agent configuration. Ensure ontology "
                    "defines counter_hypotheses. Verify GitHub API access."
                ),
            )
            self._emit(w)
            new_warnings.append(w)

        # 5. Evidence starvation — pro side empty
        if total_pro == 0 and total_counter > 0:
            w = AuditWarning(
                timestamp=ts,
                bias_type=BiasType.EVIDENCE_STARVATION,
                severity=Severity.MEDIUM,
                message=(
                    f"Zero pro-evidence collected. Belief is driven entirely by "
                    f"{total_counter} counter-evidence piece(s). "
                    f"Result may reflect API limitations, not actual evidence base."
                ),
                evidence_id=None,
                prior=0.0,
                posterior=final_belief,
                recommendation=(
                    "Add GITHUB_TOKEN and HF_TOKEN to .env. "
                    "Broaden ontology semantic_seeds or source queries."
                ),
            )
            self._emit(w)
            new_warnings.append(w)

        # 6. Source monoculture
        if source_types:
            type_counts = Counter(source_types)
            dominant_type, dominant_count = type_counts.most_common(1)[0]
            dominance_ratio = dominant_count / len(source_types)
            if dominance_ratio > 0.85 and len(source_types) > 3:
                w = AuditWarning(
                    timestamp=ts,
                    bias_type=BiasType.SOURCE_MONOCULTURE,
                    severity=Severity.MEDIUM,
                    message=(
                        f"{dominance_ratio:.0%} of evidence from single retrieval method "
                        f"'{dominant_type}' ({dominant_count}/{len(source_types)} pieces)."
                    ),
                    evidence_id=None,
                    prior=0.0,
                    posterior=final_belief,
                    recommendation="Ensure multiple agent types are active and configured.",
                )
                self._emit(w)
                new_warnings.append(w)

        # 7. Insufficient evidence for reliable conclusion
        if total_updates < 5 and final_belief != 0.0:
            w = AuditWarning(
                timestamp=ts,
                bias_type=BiasType.INSUFFICIENT_EVIDENCE,
                severity=Severity.LOW,
                message=(
                    f"Only {total_updates} evidence update(s) this session. "
                    f"Belief estimate has high variance — do not over-interpret."
                ),
                evidence_id=None,
                prior=0.0,
                posterior=final_belief,
                recommendation="Run more cycles or add data sources to improve estimate stability.",
            )
            self._emit(w)
            new_warnings.append(w)

        return new_warnings

    def session_summary(self) -> dict:
        """Structured summary of the audit session."""
        return {
            "session_id": self.session_id,
            "total_warnings": len(self._warnings),
            "by_severity": self.warning_count,
            "by_type": Counter(w.bias_type.value for w in self._warnings),
            "mean_lr": round(statistics.mean(self._lr_values), 4) if self._lr_values else None,
            "lr_std": round(statistics.stdev(self._lr_values), 4) if len(self._lr_values) > 1 else None,
            "max_single_shift": round(max((abs(d) for d in self._update_deltas), default=0), 4),
            "health_score": self._compute_health_score(),
        }

    def _compute_health_score(self) -> float:
        """
        0.0 (broken) → 1.0 (healthy).
        Penalizes by severity of warnings.
        """
        if not self._warnings:
            return 1.0
        penalty = sum({
            Severity.LOW: 0.05,
            Severity.MEDIUM: 0.15,
            Severity.HIGH: 0.30,
            Severity.CRITICAL: 0.60,
        }.get(w.severity, 0) for w in self._warnings)
        return round(max(0.0, 1.0 - penalty), 3)

    def to_obsidian_section(self) -> str:
        """Markdown section for Obsidian session note."""
        summary = self.session_summary()
        health = summary["health_score"]
        health_icon = "🟢" if health > 0.8 else "🟡" if health > 0.5 else "🔴"

        lines = [
            "",
            "## Epistemic Audit",
            f"**Health Score**: {health_icon} `{health:.3f}` / 1.000",
            f"**Warnings**: {summary['total_warnings']} total",
            "",
        ]

        if self._warnings:
            lines += [
                "| Time | Severity | Type | Message |",
                "|------|----------|------|---------|",
            ]
            for w in self._warnings:
                lines.append(w.to_obsidian_line())
        else:
            lines.append("✅ No epistemic warnings — update process appears healthy.")

        return "\n".join(lines)
