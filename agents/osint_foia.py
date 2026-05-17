"""
IrsanAI-VERA — FOIA.gov OSINT Agent
agents/osint_foia.py

Searches FOIA.gov for government requests related to the domain ontology.
Real government FOIA requests = highest provenance quality available.

- No API key required
- Public US government data
- Endpoint: https://www.foia.gov/api/search.json
"""

from __future__ import annotations

import datetime
import hashlib
import time
from typing import Optional

import requests

from core.bayesian.updater import Evidence
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology

FOIA_SEARCH_API = "https://www.foia.gov/api/search.json"
AGENT_NAME = "FOIA_OSINT_AGENT"


class FOIAOSINTAgent:
    """
    Searches FOIA.gov for government requests matching domain ontology.
    
    FOIA (Freedom of Information Act) requests are citizens asking
    the US government to release documents. Each request is a real
    signal of investigative interest and government activity.
    
    Provenance quality: VERY HIGH — official government database.
    """

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id

    def _make_evidence_id(self, request_id: str) -> str:
        hash_part = hashlib.md5(request_id.encode()).hexdigest()[:6].upper()
        return f"EVD-FOIA-{datetime.datetime.now().strftime('%Y%m%d')}-{hash_part}"

    def _score_request(self, req: dict) -> float:
        """Score FOIA request relevance against ontology seeds."""
        text = " ".join([
            req.get("title", "") or "",
            req.get("summary", "") or "",
            req.get("agency_name", "") or "",
            req.get("keywords", "") or "",
        ]).lower()

        score = 0.0
        for seed in self.ontology.semantic_seeds_high:
            if seed.lower() in text:
                score += 0.40
        for seed in self.ontology.semantic_seeds_medium:
            if seed.lower() in text:
                score += 0.20
        for seed in self.ontology.semantic_seeds_low:
            if seed.lower() in text:
                score += 0.08

        # Bonus: recent requests signal active investigation
        date_str = req.get("date_submitted", "") or ""
        if "2024" in date_str or "2025" in date_str or "2026" in date_str:
            score += 0.15

        return min(1.0, score)

    def _build_queries(self) -> list[str]:
        """Build FOIA-specific queries from ontology + supplemental."""
        queries = list(self.ontology.sources.github_queries[:3])  # reuse domain queries
        supplemental = [
            "unidentified aerial phenomena",
            "UAP disclosure",
            "AARO report",
            "UFO government",
            "non-human intelligence",
        ]
        return queries + supplemental

    def _search(self, query: str, limit: int = 10) -> list[dict]:
        """Query FOIA.gov search API."""
        params = {
            "q": query,
            "limit": limit,
            "offset": 0,
        }
        try:
            r = requests.get(
                FOIA_SEARCH_API, params=params,
                timeout=12,
                headers={"User-Agent": "IrsanAI-VERA/0.4.0 (research tool)"},
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("data", []) or []
            return []
        except requests.Timeout:
            return []
        except Exception:
            return []

    def run(self) -> list[Evidence]:
        """Run FOIA search and return scored Evidence objects."""
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.SEARCH,
            payload={"status": "starting", "source": "foia.gov"},
            confidence=1.0,
        ))

        all_evidence: list[Evidence] = []
        seen_ids: set[str] = set()
        queries = self._build_queries()

        for query in queries:
            results = self._search(query)
            time.sleep(0.5)  # respectful rate limiting

            for req in results:
                req_id = req.get("id", "") or req.get("tracking_number", "")
                if not req_id or req_id in seen_ids:
                    continue
                seen_ids.add(req_id)

                score = self._score_request(req)
                if score < 0.08:
                    continue

                agency = req.get("agency_name", "Unknown Agency")
                title = req.get("title", "Untitled Request")[:120]
                date_sub = req.get("date_submitted", "")[:10]
                status = req.get("status", "")

                ev = Evidence(
                    id=self._make_evidence_id(req_id),
                    source_url=f"https://www.foia.gov/request/{req_id}",
                    source_type="foia_gov_request",
                    source_trust_weight=0.75,  # high: official government database
                    retrieval_method="foia_api",
                    retrieved_at=datetime.datetime.now().isoformat(),
                    semantic_score=score,
                    supports_hypothesis=True,
                    summary=(
                        f"FOIA request to {agency}: '{title}' "
                        f"(submitted: {date_sub}, status: {status})"
                    ),
                    raw_snippet=req.get("summary", "")[:200] or None,
                )
                all_evidence.append(ev)

                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE, intent=Intent.SEARCH,
                    payload={
                        "evidence_id": ev.id,
                        "agency": agency,
                        "title": title[:60],
                        "score": round(score, 3),
                        "query": query,
                    },
                    confidence=score,
                ))

        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.SEARCH,
            payload={"total_found": len(all_evidence), "queries_run": len(queries)},
            confidence=0.90 if all_evidence else 0.40,
        ))

        return all_evidence
