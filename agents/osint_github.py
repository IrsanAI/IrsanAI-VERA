"""
IrsanAI-VERA — GitHub OSINT Agent
agents/osint_github.py

Searches GitHub for repositories relevant to the domain.
Uses the GitHub Search API with quality filtering (stars, recency).
Returns real Evidence objects with provenance.
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

GITHUB_SEARCH_API = "https://api.github.com/search/repositories"
AGENT_NAME = "GITHUB_OSINT_AGENT"


class GitHubOSINTAgent:
    """
    Searches GitHub for domain-relevant repositories.

    Quality filters applied:
    - Minimum star count from ontology
    - Not archived repos
    - Pushed within last 2 years (active, not dead)
    - Description and README language scoring
    """

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str,
                 github_token: Optional[str] = None):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id
        self._token = github_token

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _make_evidence_id(self, source_url: str) -> str:
        hash_part = hashlib.md5(source_url.encode()).hexdigest()[:6].upper()
        date_part = datetime.datetime.now().strftime("%Y%m%d")
        return f"EVD-GH-{date_part}-{hash_part}"

    def _is_recent_enough(self, pushed_at: str) -> bool:
        """Repos not touched in 2 years are deprioritized."""
        try:
            pushed = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            age_days = (datetime.datetime.now(datetime.timezone.utc) - pushed).days
            return age_days < 730
        except Exception:
            return True

    def _score_repo(self, repo: dict) -> float:
        """Score a repo for domain relevance."""
        text = (
            (repo.get("name") or "") + " " +
            (repo.get("description") or "") + " " +
            (repo.get("full_name") or "")
        ).lower()

        high_hits = sum(1 for s in self.ontology.semantic_seeds_high if s.lower() in text)
        med_hits  = sum(1 for s in self.ontology.semantic_seeds_medium if s.lower() in text)
        low_hits  = sum(1 for s in self.ontology.semantic_seeds_low if s.lower() in text)

        score = (high_hits * 0.35) + (med_hits * 0.15) + (low_hits * 0.05)

        # Star bonus (logarithmic — a repo with 1000 stars ≠ 10x better than 100)
        stars = repo.get("stargazers_count", 0) or 0
        if stars > 0:
            import math
            score += min(0.25, math.log10(stars + 1) / 4)

        return min(1.0, score)

    def _search(self, query: str) -> list[dict]:
        """Single GitHub API search."""
        min_stars = self.ontology.sources.github_min_stars
        full_query = f"{query} stars:>={min_stars}"
        params = {
            "q": full_query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(self.ontology.sources.github_max_results, 30),
        }
        try:
            r = requests.get(GITHUB_SEARCH_API, params=params, headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return r.json().get("items", [])
            elif r.status_code == 403:
                # Rate limit — wait and note it
                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.ERROR, intent=Intent.SEARCH,
                    payload={"error": "GitHub rate limit hit", "query": query},
                    confidence=1.0,
                ))
            return []
        except requests.RequestException as e:
            return []

    def run(self) -> list[Evidence]:
        """Execute GitHub OSINT sweep."""
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.SEARCH,
            payload={"status": "starting", "queries": self.ontology.sources.github_queries},
            confidence=1.0,
        ))

        all_evidence: list[Evidence] = []
        seen_urls: set[str] = set()

        for query in self.ontology.sources.github_queries:
            results = self._search(query)
            time.sleep(1.0)  # GitHub rate limit: 10 requests/min unauthenticated

            for repo in results:
                url = repo.get("html_url", "")
                if not url or url in seen_urls:
                    continue
                if repo.get("archived"):
                    continue
                if not self._is_recent_enough(repo.get("pushed_at", "")):
                    continue

                seen_urls.add(url)
                score = self._score_repo(repo)

                if score < 0.05:
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
                        f"GitHub repo '{repo.get('full_name')}' — {repo.get('stargazers_count', 0)} stars. "
                        f"Query: '{query}'. "
                        f"Last active: {repo.get('pushed_at', 'unknown')[:10]}."
                    ),
                    raw_snippet=(repo.get("description") or "")[:200] or None,
                )
                all_evidence.append(ev)

                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE, intent=Intent.SEARCH,
                    payload={
                        "evidence_id": ev.id,
                        "repo": repo.get("full_name"),
                        "stars": repo.get("stargazers_count", 0),
                        "score": round(score, 4),
                    },
                    confidence=score,
                ))

        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.SEARCH,
            payload={"total_found": len(all_evidence), "queries_run": len(self.ontology.sources.github_queries)},
            confidence=0.95 if all_evidence else 0.60,
        ))

        return all_evidence
