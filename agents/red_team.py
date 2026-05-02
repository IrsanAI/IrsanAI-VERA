"""
IrsanAI-VERA — Red Team Agent (Adversarial)
agents/red_team.py

The Red Team Agent is the most important agent in VERA.
Its sole purpose: actively seek evidence AGAINST the main hypothesis.

Without adversarial challenge, any system converges toward confirmation bias.
The Red Team Agent is what separates VERA from a search engine with a narrative.

Every finding it returns is marked supports_hypothesis=False,
which causes the Bayesian updater to LOWER the belief probability.
This is mathematically correct and epistemically essential.
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

AGENT_NAME = "RED_TEAM_AGENT"

# Counter-evidence search strategy: these queries actively look for
# conventional explanations, debunkings, and alternative hypotheses.
COUNTER_QUERY_TEMPLATES = [
    "{domain} debunked conventional explanation",
    "{domain} misidentification prosaic cause",
    "{domain} skeptical analysis peer reviewed",
    "alternative explanation {domain} atmospheric technical",
    "{domain} confirmation bias motivated reasoning",
]


class RedTeamAgent:
    """
    Adversarial agent — always argues against the main hypothesis.
    Searches for counter-evidence, alternative explanations, and debunkings.

    Operates on the same source APIs as the OSINT agents,
    but with inverted search strategy and inverted evidence polarity.
    """

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id

    def _make_evidence_id(self, source_url: str) -> str:
        hash_part = hashlib.md5(source_url.encode()).hexdigest()[:6].upper()
        date_part = datetime.datetime.now().strftime("%Y%m%d")
        return f"EVD-RT-{date_part}-{hash_part}"

    def _score_counter_relevance(self, text: str) -> float:
        """
        Score text for counter-evidence relevance.
        Looks for skeptical/explanatory language.
        """
        skeptical_terms = [
            "debunk", "explained", "misidentification", "conventional",
            "atmospheric", "false positive", "cognitive bias", "prosaic",
            "no evidence", "insufficient evidence", "peer review rejection",
            "extraordinary claims", "burden of proof",
        ]
        text_lower = text.lower()
        hits = sum(1 for term in skeptical_terms if term in text_lower)
        return min(1.0, hits * 0.15)

    def _search_github_counter(self) -> list[Evidence]:
        """Search GitHub for skeptical/debunking repositories."""
        domain_slug = self.ontology.domain.lower().split()[0]  # e.g., "uap"
        evidence_list = []
        seen: set[str] = set()

        for template in COUNTER_QUERY_TEMPLATES[:2]:  # Limit to avoid rate limits
            query = template.format(domain=domain_slug)
            try:
                r = requests.get(
                    "https://api.github.com/search/repositories",
                    params={"q": query, "sort": "stars", "per_page": 5},
                    headers={"Accept": "application/vnd.github+json"},
                    timeout=12,
                )
                time.sleep(1.2)

                if r.status_code != 200:
                    continue

                for repo in r.json().get("items", []):
                    url = repo.get("html_url", "")
                    if not url or url in seen:
                        continue
                    seen.add(url)

                    desc = (repo.get("description") or "").lower()
                    score = self._score_counter_relevance(
                        repo.get("name", "") + " " + desc
                    )
                    if score < 0.05:
                        score = 0.10  # Minimum signal for adversarial finds

                    ev = Evidence(
                        id=self._make_evidence_id(url),
                        source_url=url,
                        source_type="github_repository",
                        source_trust_weight=0.35,
                        retrieval_method="github_api_red_team",
                        retrieved_at=datetime.datetime.now().isoformat(),
                        semantic_score=score,
                        supports_hypothesis=False,  # ← ADVERSARIAL: lowers belief
                        summary=(
                            f"[RED TEAM] Counter-evidence repo: '{repo.get('full_name')}'. "
                            f"Stars: {repo.get('stargazers_count', 0)}. "
                            f"Represents alternative/skeptical perspective."
                        ),
                        raw_snippet=(repo.get("description") or "")[:200] or None,
                    )
                    evidence_list.append(ev)

            except requests.RequestException:
                continue

        return evidence_list

    def _generate_structural_counter_evidence(self) -> list[Evidence]:
        """
        Generate structural counter-evidence from the ontology's own
        defined counter-hypotheses. These are domain-expert skeptical positions.
        They carry moderate weight because they represent known alternative explanations.
        """
        evidence_list = []
        for i, hypothesis in enumerate(self.ontology.red_team_hypotheses):
            ev_id = f"EVD-RT-STRUCT-{datetime.datetime.now().strftime('%Y%m%d')}-{i:03d}"
            ev = Evidence(
                id=ev_id,
                source_url=f"ontology://red_team/hypothesis/{i}",
                source_type="structured_counter_hypothesis",
                source_trust_weight=0.50,  # Domain-expert level
                retrieval_method="ontology_red_team",
                retrieved_at=datetime.datetime.now().isoformat(),
                semantic_score=0.30,  # Moderate signal — not zero, but not strong
                supports_hypothesis=False,  # ← ADVERSARIAL
                summary=f"[RED TEAM] Structured counter-hypothesis: {hypothesis}",
                raw_snippet=hypothesis[:200],
            )
            evidence_list.append(ev)

        return evidence_list

    def run(self) -> list[Evidence]:
        """Execute the Red Team adversarial sweep."""
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.CHALLENGE,
            payload={"status": "starting", "mode": "adversarial"},
            confidence=1.0,
        ))

        all_counter_evidence: list[Evidence] = []

        # 1. Structural counter-evidence from ontology
        structural = self._generate_structural_counter_evidence()
        all_counter_evidence.extend(structural)

        # 2. Live GitHub counter-search
        github_counter = self._search_github_counter()
        all_counter_evidence.extend(github_counter)

        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.CHALLENGE,
            payload={
                "counter_evidence_count": len(all_counter_evidence),
                "structural_hypotheses": len(structural),
                "live_found": len(github_counter),
                "note": "All findings are adversarial — they will LOWER belief probability.",
            },
            confidence=0.90,
        ))

        return all_counter_evidence
