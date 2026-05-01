"""
IrsanAI-VERA — Bayesian Belief Updater
core/bayesian/updater.py

The only component allowed to produce probability values.
Every update requires a real Evidence object with provenance.
No hardcoded numbers. No simulated signals.
"""

from __future__ import annotations

import json
import math
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Evidence:
    """
    A single piece of evidence with full provenance chain.
    This is the atomic unit of truth in VERA.
    """
    id: str                           # Unique identifier: EVD-YYYYMMDD-NNN
    source_url: str                   # Direct URL or identifier — required
    source_type: str                  # From ontology: "FOIA_release", "news_article", etc.
    source_trust_weight: float        # From ontology entity config (0.0 – 1.0)
    retrieval_method: str             # "hf_api", "github_api", "rss_feed", "manual"
    retrieved_at: str                 # ISO timestamp
    semantic_score: float             # NLP semantic similarity score (0.0 – 1.0)
    supports_hypothesis: bool         # True = pro-evidence, False = counter-evidence (Red Team)
    summary: str                      # Human-readable description of what was found
    raw_snippet: Optional[str] = None # Up to 200 chars of original text
    corroborated_by: list[str] = field(default_factory=list)  # Other EVD IDs

    def likelihood_ratio(self) -> float:
        """
        Bayes factor for this piece of evidence.
        P(Evidence | H is true) / P(Evidence | H is false)

        High trust + high semantic score + corroboration = strong update.
        Counter-evidence (Red Team) returns inverse ratio.
        """
        base_lr = self.source_trust_weight * self.semantic_score
        corroboration_bonus = 1.0 + (len(self.corroborated_by) * 0.15)
        lr = base_lr * corroboration_bonus

        # Age decay: evidence older than 90 days loses weight
        retrieved = datetime.datetime.fromisoformat(self.retrieved_at)
        age_days = (datetime.datetime.now() - retrieved).days
        if age_days > 90:
            lr *= max(0.3, 1.0 - ((age_days - 90) / 365))

        if not self.supports_hypothesis:
            # Counter-evidence: invert the ratio
            return 1.0 / max(lr, 0.01)

        return max(lr, 0.01)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_obsidian_note(self) -> str:
        """Generate a markdown note for Obsidian vault."""
        direction = "✅ PRO" if self.supports_hypothesis else "❌ COUNTER (Red Team)"
        return f"""---
tags: [vera/evidence, vera/{self.source_type}]
vera_id: {self.id}
retrieved: {self.retrieved_at}
trust: {self.source_trust_weight}
semantic_score: {self.semantic_score:.3f}
direction: {"pro" if self.supports_hypothesis else "counter"}
---

# {self.id} — {direction}

## Summary
{self.summary}

## Provenance
- **Source**: [{self.source_url}]({self.source_url})
- **Type**: `{self.source_type}`
- **Method**: `{self.retrieval_method}`
- **Retrieved**: {self.retrieved_at}
- **Trust Weight**: {self.source_trust_weight}

## Signal Strength
- **Semantic Score**: {self.semantic_score:.3f}
- **Likelihood Ratio**: {self.likelihood_ratio():.4f}

## Corroborated By
{chr(10).join(f"- [[{eid}]]" for eid in self.corroborated_by) or "- No corroboration yet"}

## Raw Snippet
> {self.raw_snippet or "No snippet available"}
"""


class BayesianBeliefUpdater:
    """
    Updates a probability estimate using Bayes theorem.
    Every update is logged. No value can be set directly from outside.
    """

    def __init__(self, prior: float, hypothesis_name: str, data_dir: Path):
        assert 0.0 < prior < 1.0, "Prior must be between 0 and 1 (exclusive)"
        self._belief = prior
        self._prior = prior
        self.hypothesis = hypothesis_name
        self.evidence_log: list[Evidence] = []
        self.data_dir = data_dir
        self._update_log_path = data_dir / "belief_updates.jsonl"

    @property
    def belief(self) -> float:
        return self._belief

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_log)

    def update(self, evidence: Evidence) -> float:
        """
        Apply Bayes theorem: posterior = (prior * likelihood) / normalizer
        Returns the new belief value.
        """
        prior = self._belief
        lr = evidence.likelihood_ratio()

        # Bayes: P(H|E) = P(E|H) * P(H) / P(E)
        # Using odds form: posterior_odds = LR * prior_odds
        prior_odds = prior / (1.0 - prior)
        posterior_odds = lr * prior_odds
        posterior = posterior_odds / (1.0 + posterior_odds)

        # Clamp to prevent extremes from single evidence
        posterior = max(0.02, min(0.98, posterior))

        self._belief = posterior
        self.evidence_log.append(evidence)

        # Log every update for auditability
        update_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "evidence_id": evidence.id,
            "prior": round(prior, 6),
            "likelihood_ratio": round(lr, 6),
            "posterior": round(posterior, 6),
            "delta": round(posterior - prior, 6),
            "supports_hypothesis": evidence.supports_hypothesis,
        }
        with open(self._update_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(update_record) + "\n")

        return posterior

    def update_batch(self, evidence_list: list[Evidence]) -> float:
        """Apply multiple evidence updates in sequence."""
        for ev in evidence_list:
            self.update(ev)
        return self._belief

    def summary(self) -> dict:
        """Current state of belief with full audit context."""
        pro_count = sum(1 for e in self.evidence_log if e.supports_hypothesis)
        counter_count = len(self.evidence_log) - pro_count

        return {
            "hypothesis": self.hypothesis,
            "prior": self._prior,
            "current_belief": round(self._belief, 4),
            "total_evidence": len(self.evidence_log),
            "pro_evidence": pro_count,
            "counter_evidence": counter_count,
            "net_shift": round(self._belief - self._prior, 4),
            "last_updated": self.evidence_log[-1].retrieved_at if self.evidence_log else None,
        }

    def verdict(self, thresholds: list[dict]) -> dict:
        """Map current belief to a human-readable verdict using ontology thresholds."""
        for threshold in sorted(thresholds, key=lambda x: x["max"]):
            if self._belief <= threshold["max"]:
                return {
                    "belief": round(self._belief, 4),
                    "label": threshold["label"],
                    "color": threshold["color"],
                }
        return {"belief": round(self._belief, 4), "label": "Unknown", "color": "gray"}
