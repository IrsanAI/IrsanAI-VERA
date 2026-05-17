"""
IrsanAI-VERA — arXiv OSINT Agent
agents/osint_arxiv.py

Searches arXiv preprint server for scientific papers matching the domain.
Scientific papers = highest credibility, full provenance (DOI, authors, abstract).

- No API key required
- Open access scientific literature
- Endpoint: http://export.arxiv.org/api/query (Atom XML)
"""

from __future__ import annotations

import datetime
import hashlib
import time
import xml.etree.ElementTree as ET
from typing import Optional

import requests

from core.bayesian.updater import Evidence
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology

ARXIV_API = "http://export.arxiv.org/api/query"
AGENT_NAME = "ARXIV_OSINT_AGENT"
NS = {"atom": "http://www.w3.org/2005/Atom"}

SUPPLEMENTAL_QUERIES = [
    "unidentified aerial phenomena UAP",
    "anomalous aerial vehicle detection",
    "UFO scientific analysis radar",
    "aerial anomaly sensor fusion",
    "government disclosure national security aerial",
]


class ArXivOSINTAgent:
    """
    Searches arXiv for scientific papers matching the domain ontology.
    
    arXiv papers have DOI, authors, abstracts, submission dates.
    This gives VERA access to peer-reviewed or preprint scientific
    perspectives — countering anecdotal evidence with data-driven analysis.
    
    Provenance quality: HIGH — academic institution submissions.
    Trust weight: 0.80 (scientific sourcing, author accountability).
    """

    def __init__(self, ontology: DomainOntology, bus: LRPBus, session_id: str):
        self.ontology = ontology
        self.bus = bus
        self.session_id = session_id

    def _make_evidence_id(self, arxiv_id: str) -> str:
        hash_part = hashlib.md5(arxiv_id.encode()).hexdigest()[:6].upper()
        return f"EVD-ARXIV-{datetime.datetime.now().strftime('%Y%m%d')}-{hash_part}"

    def _score_paper(self, title: str, abstract: str) -> float:
        """Score paper relevance against ontology seeds."""
        text = (title + " " + abstract).lower()
        score = 0.0

        for seed in self.ontology.semantic_seeds_high:
            if seed.lower() in text:
                score += 0.35
        for seed in self.ontology.semantic_seeds_medium:
            if seed.lower() in text:
                score += 0.18
        for seed in self.ontology.semantic_seeds_low:
            if seed.lower() in text:
                score += 0.08

        # Scientific methodology bonus
        science_markers = ["sensor", "radar", "infrared", "spectral",
                           "detection", "measurement", "analysis", "data"]
        for marker in science_markers:
            if marker in text:
                score += 0.04

        return min(1.0, score)

    def _search(self, query: str, max_results: int = 8) -> list[dict]:
        """Query arXiv API and parse Atom XML response."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            r = requests.get(
                ARXIV_API, params=params,
                timeout=15,
                headers={"User-Agent": "IrsanAI-VERA/0.4.0 (research tool)"},
            )
            if r.status_code != 200:
                return []

            root = ET.fromstring(r.content)
            papers = []

            for entry in root.findall("atom:entry", NS):
                def get(tag: str) -> str:
                    el = entry.find(f"atom:{{http://www.w3.org/2005/Atom}}{tag}", NS)
                    if el is None:
                        el = entry.find(tag)
                    return (el.text or "").strip() if el is not None else ""

                arxiv_id_url = get("id")
                title = get("title").replace("\n", " ").strip()
                abstract = get("summary").replace("\n", " ").strip()
                published = get("published")[:10]

                authors = []
                for author in entry.findall("atom:author", NS):
                    name_el = author.find("atom:name", NS)
                    if name_el is not None and name_el.text:
                        authors.append(name_el.text.strip())

                papers.append({
                    "id": arxiv_id_url,
                    "title": title,
                    "abstract": abstract[:400],
                    "published": published,
                    "authors": authors[:3],
                    "url": arxiv_id_url,
                })

            return papers

        except ET.ParseError:
            return []
        except requests.Timeout:
            return []
        except Exception:
            return []

    def run(self) -> list[Evidence]:
        """Run arXiv search and return scored Evidence objects."""
        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.HEARTBEAT, intent=Intent.SEARCH,
            payload={"status": "starting", "source": "arxiv.org"},
            confidence=1.0,
        ))

        all_evidence: list[Evidence] = []
        seen_ids: set[str] = set()

        # Combine ontology queries with supplemental
        queries = (
            self.ontology.sources.github_queries[:2]
            + SUPPLEMENTAL_QUERIES
        )

        for query in queries:
            papers = self._search(query)
            time.sleep(3.0)  # arXiv requests: be respectful, 3s between calls

            for paper in papers:
                paper_id = paper["id"]
                if not paper_id or paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)

                score = self._score_paper(paper["title"], paper["abstract"])
                if score < 0.08:
                    continue

                authors_str = ", ".join(paper["authors"]) or "Unknown"
                title_short = paper["title"][:100]

                ev = Evidence(
                    id=self._make_evidence_id(paper_id),
                    source_url=paper["url"],
                    source_type="arxiv_paper",
                    source_trust_weight=0.80,  # academic sourcing
                    retrieval_method="arxiv_api",
                    retrieved_at=datetime.datetime.now().isoformat(),
                    semantic_score=score,
                    supports_hypothesis=True,
                    summary=(
                        f"arXiv: '{title_short}' by {authors_str} "
                        f"(published: {paper['published']})"
                    ),
                    raw_snippet=paper["abstract"][:200] or None,
                )
                all_evidence.append(ev)

                self.bus.send(self.bus.create_message(
                    sender=AGENT_NAME, receiver="ORCHESTRATOR",
                    msg_type=MessageType.EVIDENCE, intent=Intent.SEARCH,
                    payload={
                        "evidence_id": ev.id,
                        "title": title_short[:60],
                        "authors": authors_str[:40],
                        "published": paper["published"],
                        "score": round(score, 3),
                        "query": query,
                    },
                    confidence=score,
                ))

        self.bus.send(self.bus.create_message(
            sender=AGENT_NAME, receiver="ORCHESTRATOR",
            msg_type=MessageType.RESULT, intent=Intent.SEARCH,
            payload={
                "total_found": len(all_evidence),
                "queries_run": len(queries),
                "unique_papers": len(seen_ids),
            },
            confidence=0.90 if all_evidence else 0.40,
        ))

        return all_evidence
