"""
IrsanAI-VERA — HuggingFace OSINT Agent v2
agents/osint_huggingface.py

v0.3.0 improvements:
- Typed error categories (rate limit / auth / timeout)
- Funnel query strategy: domain-specific → broader fallback
- Better relevance scoring (seed density + quality signals)
- HF_TOKEN from .env
- Graceful degradation when API unavailable
"""

from __future__ import annotations

import datetime
import hashlib
import os
import time
from typing import Optional

import requests

from core.bayesian.updater import Evidence
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology

HF_DATASET_API = "https://huggingface.co/api/datasets"
AGENT_NAME = "HF_OSINT_AGENT"

FALLBACK_QUERIES = [
    "government documents declassified",
    "intelligence agency reports",
    "FOIA freedom of information",
    "military anomaly detection",
    "national security archive",
]


class HuggingFaceOSINTAgent:
    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id
        self._hf_token: Optional[str] = os.environ.get("HF_TOKEN")

    def _headers(self) -> dict:
        h = {"Accept": "application/json", "User-Agent": "IrsanAI-VERA/0.3.0"}
        if self._hf_token:
            h["Authorization"] = f"Bearer {self._hf_token}"
        return h

    def _make_evidence_id(self, source_url: str) -> str:
        hash_part = hashlib.md5(source_url.encode()).hexdigest()[:6].upper()
        return f"EVD-HF-{datetime.datetime.now().strftime('%Y%m%d')}-{hash_part}"

    def _search_datasets(self, query: str, limit: int = 10) -> list[dict]:
        params = {"search": query, "sort": "likes", "direction": -1, "limit": limit, "full": "true"}
        try:
            r = requests.get(HF_DATASET_API, params=params, headers=self._headers(), timeout=15)
            if r.status_code == 200 and r.text.strip():
                return r.json()
            if r.status_code == 429:
                self._send_error("HF rate limit hit — set HF_TOKEN in .env for higher limits", query)
                time.sleep(60)
            elif r.status_code == 403:
                self._send_error("HF auth error — set HF_TOKEN in .env", query)
            return []
        except requests.Timeout:
            self._send_error("HF timeout", query)
            return []
        except Exception:
            return []

    def _send_error(self, msg: str, query: str):
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.ERROR, intent=Intent.SEARCH,
            payload={"error": msg, "query": query}, confidence=1.0,
        ))

    def _score_dataset(self, dataset: dict) -> tuple[float, list[str]]:
        text = " ".join([
            dataset.get("id") or "",
            dataset.get("description") or "",
            " ".join(dataset.get("tags") or []),
        ]).lower()

        matched, score = [], 0.0
        for seed in self.ontology.semantic_seeds_high:
            if seed.lower() in text:
                score += 0.40; matched.append(f"HIGH:{seed}")
        for seed in self.ontology.semantic_seeds_medium:
            if seed.lower() in text:
                score += 0.20; matched.append(f"MED:{seed}")
        for seed in self.ontology.semantic_seeds_low:
            if seed.lower() in text:
                score += 0.08; matched.append(f"LOW:{seed}")

        likes = dataset.get("likes", 0) or 0
        score += 0.15 if likes > 50 else (0.08 if likes > 10 else 0)
        score += 0.10 if (dataset.get("downloads") or 0) > 1000 else 0

        return min(1.0, score), matched

    def run(self) -> list[Evidence]:
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.SEARCH,
            payload={"status": "starting", "token_set": bool(self._hf_token)},
            confidence=1.0,
        ))

        all_evidence, seen_ids = [], set()

        for query in self.ontology.sources.hf_queries + FALLBACK_QUERIES:
            for ds in self._search_datasets(query, limit=self.ontology.sources.hf_max_results):
                ds_id = ds.get("id", "")
                if not ds_id or ds_id in seen_ids:
                    continue
                seen_ids.add(ds_id)

                score, matched = self._score_dataset(ds)
                if score < 0.06:
                    continue

                source_url = f"https://huggingface.co/datasets/{ds_id}"
                ev = Evidence(
                    id=self._make_evidence_id(source_url),
                    source_url=source_url,
                    source_type="hf_dataset",
                    source_trust_weight=0.45,
                    retrieval_method="hf_api",
                    retrieved_at=datetime.datetime.now().isoformat(),
                    semantic_score=score,
                    supports_hypothesis=True,
                    summary=(
                        f"HuggingFace dataset '{ds_id}' matched query '{query}'. "
                        f"Seeds: {', '.join(matched[:3])}. Likes: {ds.get('likes', 0)}."
                    ),
                    raw_snippet=(ds.get("description") or "")[:200] or None,
                )
                all_evidence.append(ev)
                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE, intent=Intent.SEARCH,
                    payload={"evidence_id": ev.id, "dataset_id": ds_id, "score": round(score, 4)},
                    confidence=score,
                ))
            time.sleep(0.8)

        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.SEARCH,
            payload={"total_found": len(all_evidence), "scanned": len(seen_ids)},
            confidence=0.95 if all_evidence else 0.50,
        ))
        return all_evidence
