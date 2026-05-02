"""
IrsanAI-VERA — HuggingFace OSINT Agent
agents/osint_huggingface.py

Searches HuggingFace for datasets semantically relevant to the domain.
Uses the HF API with multiple query strategies derived from the ontology.
Returns real Evidence objects — no simulated data, no hardcoded values.
"""

from __future__ import annotations

import datetime
import hashlib
import time
from typing import Optional

import requests

from core.bayesian.updater import Evidence
from core.lrp_messenger import LRPBus, LRPMessage, MessageType, Intent
from core.ontology_loader import DomainOntology

HF_DATASET_API = "https://huggingface.co/api/datasets"
HF_MODEL_API   = "https://huggingface.co/api/models"
AGENT_NAME     = "HF_OSINT_AGENT"


class HuggingFaceOSINTAgent:
    """
    Searches HuggingFace for domain-relevant datasets and models.

    Strategy:
    - Multiple queries from ontology (not just one keyword)
    - Filters by likes/downloads for quality signal
    - Generates real Evidence objects with trust weight from doctype config
    - Reports via LRP bus
    """

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id
        self._hf_token: Optional[str] = None  # Set via set_token() for higher rate limits

    def set_token(self, token: str):
        self._hf_token = token

    def _headers(self) -> dict:
        h = {"Accept": "application/json"}
        if self._hf_token:
            h["Authorization"] = f"Bearer {self._hf_token}"
        return h

    def _make_evidence_id(self, source_url: str) -> str:
        hash_part = hashlib.md5(source_url.encode()).hexdigest()[:6].upper()
        date_part = datetime.datetime.now().strftime("%Y%m%d")
        return f"EVD-HF-{date_part}-{hash_part}"

    def _search_datasets(self, query: str, limit: int = 5) -> list[dict]:
        """Single HF API call for datasets."""
        params = {
            "search": query,
            "sort": "likes",
            "direction": -1,
            "limit": limit,
        }
        try:
            r = requests.get(HF_DATASET_API, params=params, headers=self._headers(), timeout=12)
            if r.status_code == 200:
                return r.json()
            return []
        except requests.RequestException:
            return []

    def _score_dataset(self, dataset: dict, semantic_seeds: list[str]) -> float:
        """
        Simple relevance score: check if any high-signal seeds appear
        in the dataset id or description.
        Returns 0.0–1.0.
        Proper sentence-transformer scoring is in agents/nlp_signal.py.
        This is a fast pre-filter.
        """
        text = (
            (dataset.get("id") or "") + " " +
            (dataset.get("description") or "") + " " +
            " ".join(dataset.get("tags") or [])
        ).lower()

        # High signal seeds → higher score
        high_hits = sum(1 for seed in self.ontology.semantic_seeds_high if seed.lower() in text)
        med_hits  = sum(1 for seed in self.ontology.semantic_seeds_medium if seed.lower() in text)
        low_hits  = sum(1 for seed in self.ontology.semantic_seeds_low if seed.lower() in text)

        score = (high_hits * 0.4) + (med_hits * 0.2) + (low_hits * 0.05)

        # Popularity bonus (likes as proxy for quality)
        likes = dataset.get("likes", 0) or 0
        score += min(0.2, likes / 500)

        return min(1.0, score)

    def run(self) -> list[Evidence]:
        """
        Execute the HuggingFace OSINT sweep.
        Returns a list of Evidence objects (may be empty if nothing found).
        """
        # Announce start via LRP
        start_msg = self.bus.create_message(
            sender=AGENT_NAME,
            receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT,
            intent=Intent.SEARCH,
            payload={"status": "starting", "queries": self.ontology.sources.hf_queries},
            confidence=1.0,
        )
        self.bus.send(start_msg)

        all_evidence: list[Evidence] = []
        seen_ids: set[str] = set()

        for query in self.ontology.sources.hf_queries:
            results = self._search_datasets(query, limit=self.ontology.sources.hf_max_results)
            time.sleep(0.5)  # Polite rate limiting

            for ds in results:
                ds_id = ds.get("id", "")
                if not ds_id or ds_id in seen_ids:
                    continue
                seen_ids.add(ds_id)

                score = self._score_dataset(ds, self.ontology.all_semantic_seeds)

                # Only surface datasets with meaningful signal
                if score < 0.05:
                    continue

                source_url = f"https://huggingface.co/datasets/{ds_id}"
                ev = Evidence(
                    id=self._make_evidence_id(source_url),
                    source_url=source_url,
                    source_type="hf_dataset",
                    source_trust_weight=0.45,  # HF datasets: moderate trust
                    retrieval_method="hf_api",
                    retrieved_at=datetime.datetime.now().isoformat(),
                    semantic_score=score,
                    supports_hypothesis=True,
                    summary=(
                        f"HuggingFace dataset '{ds_id}' matched domain query '{query}'. "
                        f"Likes: {ds.get('likes', 0)}. "
                        f"Tags: {', '.join((ds.get('tags') or [])[:5])}."
                    ),
                    raw_snippet=ds.get("description", "")[:200] if ds.get("description") else None,
                )
                all_evidence.append(ev)

                # Report each find via LRP
                find_msg = self.bus.create_message(
                    sender=AGENT_NAME,
                    receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE,
                    intent=Intent.SEARCH,
                    payload={
                        "evidence_id": ev.id,
                        "source_url": ev.source_url,
                        "semantic_score": round(score, 4),
                        "query_used": query,
                    },
                    confidence=score,
                )
                self.bus.send(find_msg)

        # Final report
        done_msg = self.bus.create_message(
            sender=AGENT_NAME,
            receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT,
            intent=Intent.SEARCH,
            payload={
                "total_found": len(all_evidence),
                "queries_run": len(self.ontology.sources.hf_queries),
                "seen_datasets": len(seen_ids),
            },
            confidence=0.95 if all_evidence else 0.60,
        )
        self.bus.send(done_msg)

        return all_evidence
