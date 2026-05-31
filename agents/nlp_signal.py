"""
IrsanAI-VERA — NLP Signal Agent v1.1 (Fixed)
agents/nlp_signal.py

FIXES in v1.1:
- Counter-evidence is NEVER filtered (Red Team output must survive)
- Threshold lowered from 0.65 to 0.20 (UAP repos score 0.15-0.45)
- Graceful fallback if sentence-transformers not available
- Configurable threshold via ontology or direct param
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.ontology_loader import DomainOntology
    from core.bayesian.updater import Evidence

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


class NLPSignalAgent:
    """
    Semantic re-scorer using sentence-transformers.

    CRITICAL RULE: Counter-evidence (supports_hypothesis=False) is
    NEVER filtered. It comes from the Red Team and must always survive.
    Only pro-evidence is subject to semantic filtering.

    Threshold: 0.20 (not 0.65 — UAP repos score 0.15-0.45 in embedding space)
    """

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        threshold: float = 0.20,
    ):
        self.threshold = threshold
        self._model = None
        self._model_name = model

        if _ST_AVAILABLE:
            try:
                self._model = SentenceTransformer(model)
            except Exception:
                self._model = None

    def _get_model(self):
        if self._model is None and _ST_AVAILABLE:
            try:
                self._model = SentenceTransformer(self._model_name)
            except Exception:
                pass
        return self._model

    def score_evidence(
        self,
        ev,
        ontology_seeds: list[str],
        threshold: float | None = None,
    ) -> float:
        """
        Compute cosine similarity between evidence text and ontology seeds.
        Returns 0.0 if below threshold (reject), else similarity score.

        Counter-evidence always returns 1.0 (never rejected).
        """
        # CRITICAL: never filter counter-evidence
        if not ev.supports_hypothesis:
            return 1.0

        model = self._get_model()
        if model is None or not ontology_seeds:
            # No model available → pass-through (don't reject)
            return ev.semantic_score if ev.semantic_score > 0 else 0.5

        t = threshold if threshold is not None else self.threshold

        text = " ".join(filter(None, [
            ev.summary or "",
            ev.raw_snippet or "",
        ])).strip()

        if not text:
            return 0.5  # no text → pass-through

        try:
            import numpy as np
            ev_emb = model.encode([text], convert_to_numpy=True)
            seed_emb = model.encode(ontology_seeds, convert_to_numpy=True)

            # Max similarity across all seeds
            similarities = np.dot(ev_emb, seed_emb.T) / (
                np.linalg.norm(ev_emb) * np.linalg.norm(seed_emb, axis=1) + 1e-8
            )
            max_sim = float(np.max(similarities))

            return max_sim if max_sim >= t else 0.0

        except Exception:
            # Any error → pass-through
            return ev.semantic_score if ev.semantic_score > 0 else 0.5

    def rescore_batch(
        self,
        evidence_list: list,
        ontology,
        threshold: float | None = None,
    ) -> list:
        """
        Filter and rescore entire evidence batch.

        Rules:
        1. Counter-evidence (supports_hypothesis=False) → ALWAYS kept
        2. Pro-evidence with score >= threshold → kept, score updated
        3. Pro-evidence with score < threshold → rejected

        Returns filtered list with updated semantic scores.
        """
        if not evidence_list:
            return evidence_list

        seeds = (
            list(ontology.semantic_seeds_high or [])
            + list(ontology.semantic_seeds_medium or [])
        )

        if not seeds:
            # No seeds defined → pass everything through
            return evidence_list

        result = []
        rejected = 0

        for ev in evidence_list:
            # Counter-evidence is SACRED — never filtered
            if not ev.supports_hypothesis:
                result.append(ev)
                continue

            score = self.score_evidence(ev, seeds, threshold)

            if score > 0.0:
                # Update the semantic score with NLP score
                ev.semantic_score = max(ev.semantic_score, score)
                result.append(ev)
            else:
                rejected += 1

        return result
