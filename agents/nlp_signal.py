"""
IrsanAI-VERA — Semantic NLP Signal Agent
agents/nlp_signal.py
"""

from __future__ import annotations
import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.bayesian.updater import Evidence
    from core.ontology_loader import DomainOntology


class NLPSignalAgent:
    """Semantic re-scorer using sentence-transformers."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model)

    def score_evidence(
        self,
        ev: Evidence,
        ontology_seeds: list[str],
        threshold: float = 0.65,
    ) -> float:
        """Cosine similarity between evidence text and seeds.
        Returns 0.0 if below threshold (REJECT), else similarity score."""
        if not ontology_seeds:
            return ev.semantic_score
            
        text = ev.summary + " " + (ev.raw_snippet or "")
        text_emb = self.model.encode(text, convert_to_tensor=True)
        seed_embs = self.model.encode(ontology_seeds, convert_to_tensor=True)
        
        # Compute cosine similarities
        cosine_scores = util.cos_sim(text_emb, seed_embs)
        max_score = float(np.max(cosine_scores.cpu().numpy()))
        
        if max_score < threshold:
            return 0.0
        return max_score

    def rescore_batch(
        self,
        evidence_list: list[Evidence],
        ontology: DomainOntology,
    ) -> list[Evidence]:
        """Filter and rescore entire evidence batch. 
        Removes false positives like iOS libraries named 'UAP'."""
        seeds = (
            ontology.semantic_seeds_high + 
            ontology.semantic_seeds_medium + 
            ontology.semantic_seeds_low
        )
        
        rescored = []
        for ev in evidence_list:
            new_score = self.score_evidence(ev, seeds)
            if new_score > 0:
                ev.semantic_score = new_score
                rescored.append(ev)
        return rescored
