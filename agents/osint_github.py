"""
IrsanAI-VERA — GitHub OSINT Agent v2.2
agents/osint_github.py

Fix v2.2:
- Memory store is now mandatory (no silent fail)
- Uses VERAMemoryStore to prevent duplicate URLs across sessions (M-002)
"""

from __future__ import annotations

import datetime
import hashlib
import math
import os
import time
from typing import Optional

import requests

from core.bayesian.updater import Evidence
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology
from core.memory.chromadb_store import VERAMemoryStore

GITHUB_SEARCH_API = "https://api.github.com/search/repositories"
AGENT_NAME = "GITHUB_OSINT_AGENT"

SUPPLEMENTAL_QUERIES = [
    "UFO sighting database",
    "UAP evidence research",
    "FOIA government secrets",
    "alien disclosure project",
    "UAP sensor anomaly",
]


class GitHubOSINTAgent:

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str,
                 github_token: Optional[str] = None):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id
        self._token = github_token or os.environ.get("GITHUB_TOKEN")
        # M-002: Memory store is now mandatory
        self.memory = VERAMemoryStore()

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "IrsanAI-VERA/0.4.0"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _make_evidence_id(self, url: str) -> str:
        hash_part = hashlib.md5(url.encode()).hexdigest()[:6].upper()
        return f"EVD-GH-{datetime.datetime.now().strftime('%Y%m%d')}-{hash_part}"

    def _is_recent(self, pushed_at: str) -> bool:
        try:
            pushed = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            return (datetime.datetime.now(datetime.timezone.utc) - pushed).days < 730
        except Exception:
            return True

    def _score_repo(self, repo: dict) -> float:
        text = " ".join([
            repo.get("name") or "",
            repo.get("description") or "",
            repo.get("full_name") or "",
            " ".join(repo.get("topics") or []),
        ]).lower()

        score = 0.0
        for seed in self.ontology.semantic_seeds_high:
            if seed.lower() in text:
                score += 0.35
        for seed in self.ontology.semantic_seeds_medium:
            if seed.lower() in text:
                score += 0.18
        for seed in self.ontology.semantic_seeds_low:
            if seed.lower() in text:
                score += 0.07

        # Stars bonus — logarithmic
        stars = repo.get("stargazers_count", 0) or 0
        if stars > 0:
            score += min(0.30, math.log10(stars + 1) / 3.5)

        return min(1.0, score)

    def _search(self, query: str) -> list[dict]:
        min_stars = max(0, self.ontology.sources.github_min_stars - 2)
        params = {
            "q": f"{query} stars:>={min_stars}",
            "sort": "stars",
            "order": "desc",
            "per_page": min(self.ontology.sources.github_max_results, 30),
        }
        try:
            r = requests.get(GITHUB_SEARCH_API, params=params,
                             headers=self._headers(), timeout=15)
            if r.status_code == 200:
                items = r.json().get("items", [])
                return items
            elif r.status_code == 403:
                remaining = r.headers.get("X-RateLimit-Remaining", "?")
                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.ERROR, intent=Intent.SEARCH,
                    payload={"error": "GitHub rate limit or auth", "remaining": remaining},
                    confidence=1.0,
                ))
            return []
        except requests.Timeout:
            return []
        except Exception:
            return []

    def run(self) -> list[Evidence]:
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.SEARCH,
            payload={"status": "starting", "token_set": bool(self._token)},
            confidence=1.0,
        ))

        all_evidence, seen_urls = [], set()
        all_queries = self.ontology.sources.github_queries + SUPPLEMENTAL_QUERIES
        total_raw = 0

        for query in all_queries:
            results = self._search(query)
            total_raw += len(results)
            time.sleep(0.8 if self._token else 2.0)

            for repo in results:
                url = repo.get("html_url", "")
                if not url or url in seen_urls or repo.get("archived"):
                    continue
                
                # M-002: Check cross-session memory - prevents duplicates
                if self.memory.has_seen_url(url):
                    continue

                if not self._is_recent(repo.get("pushed_at", "")):
                    continue
                seen_urls.add(url)

                score = self._score_repo(repo)

                # Accept any repo with stars bonus alone (score >= 0.01)
                if score < 0.01:
                    continue

                ev = Evidence(
                    id=self._make_evidence_id(url),
                    source_url=url,
                    source_type="github_repository",
                    source_trust_weight=0.40,
                    retrieval_method="github_api",
                    retrieved_at=datetime.datetime.now().isoformat(),
                    semantic_score=score,
                    supports_hypothesis=True,
                    summary=(
                        f"GitHub: '{repo.get('full_name')}' — "
                        f"{repo.get('stargazers_count', 0)}★ — query: '{query}'."
                    ),
                    raw_snippet=(repo.get("description") or "")[:200] or None,
                )
                all_evidence.append(ev)
                
                # M-002: Store in memory for cross-session deduplication
                self.memory.store_evidence(ev, self.session_id)

                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE, intent=Intent.SEARCH,
                    payload={
                        "evidence_id": ev.id,
                        "repo": repo.get("full_name"),
                        "stars": repo.get("stargazers_count", 0),
                        "score": round(score, 4),
                        "query": query,
                    },
                    confidence=score,
                ))

        # Debug: report raw results count
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.SEARCH,
            payload={
                "total_found": len(all_evidence),
                "total_raw_api_results": total_raw,
                "queries_run": len(all_queries),
                "unique_checked": len(seen_urls),
            },
            confidence=0.95 if all_evidence else 0.50,
        ))

        return all_evidence
