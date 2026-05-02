"""
IrsanAI-VERA — Ontology Loader
core/ontology_loader.py

Reads a domain YAML file and returns a typed config object.
This is the single point of domain customization.
Swap the YAML → entire system changes domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class EntityConfig:
    name: str
    trust_weight: float
    full_name: str = ""


@dataclass
class BayesianConfig:
    prior_tech_coverup: float
    prior_et_presence: float
    min_evidence_for_update: int
    confidence_decay_days: int


@dataclass
class SourceConfig:
    github_queries: list[str]
    github_max_results: int
    github_min_stars: int
    hf_queries: list[str]
    hf_max_results: int
    rss_feeds: list[dict]


@dataclass
class VerdictThreshold:
    max: float
    label: str
    color: str


@dataclass
class ObsidianConfig:
    link_threshold: float
    tags: list[str]


@dataclass
class DomainOntology:
    """Fully typed domain configuration loaded from a YAML file."""
    domain: str
    version: str
    description: str

    bayesian: BayesianConfig
    entities: list[EntityConfig]
    document_types: list[EntityConfig]

    semantic_seeds_high: list[str]
    semantic_seeds_medium: list[str]
    semantic_seeds_low: list[str]

    sources: SourceConfig
    red_team_hypotheses: list[str]
    red_team_sources: list[str]

    verdict_thresholds: list[VerdictThreshold]
    obsidian: ObsidianConfig

    @property
    def all_semantic_seeds(self) -> list[str]:
        return self.semantic_seeds_high + self.semantic_seeds_medium + self.semantic_seeds_low

    @property
    def entity_trust_map(self) -> dict[str, float]:
        return {e.name: e.trust_weight for e in self.entities}

    @property
    def doctype_trust_map(self) -> dict[str, float]:
        return {d.name: d.trust_weight for d in self.document_types}

    def get_verdict(self, belief: float) -> VerdictThreshold:
        for threshold in sorted(self.verdict_thresholds, key=lambda x: x.max):
            if belief <= threshold.max:
                return threshold
        return self.verdict_thresholds[-1]


def load_ontology(path: Path) -> DomainOntology:
    """
    Load and validate a domain ontology YAML file.
    Raises clear errors if required fields are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Ontology file not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # ---- Meta ----
    meta = raw.get("meta", {})
    domain = meta.get("domain", path.stem)
    version = meta.get("version", "1.0")
    description = meta.get("description", "")

    # ---- Bayesian ----
    b = raw.get("bayesian", {})
    bayesian = BayesianConfig(
        prior_tech_coverup=b.get("prior_tech_coverup", 0.10),
        prior_et_presence=b.get("prior_et_presence", 0.05),
        min_evidence_for_update=b.get("min_evidence_for_update", 3),
        confidence_decay_days=b.get("confidence_decay_days", 90),
    )

    # ---- Entities ----
    entities = [
        EntityConfig(
            name=e["name"],
            trust_weight=e.get("trust_weight", 0.5),
            full_name=e.get("full_name", e["name"]),
        )
        for e in raw.get("entities", {}).get("organizations", [])
    ]
    document_types = [
        EntityConfig(
            name=d["type"],
            trust_weight=d.get("trust_weight", 0.5),
        )
        for d in raw.get("entities", {}).get("document_types", [])
    ]

    # ---- Semantic Seeds ----
    seeds = raw.get("semantic_seeds", {})
    semantic_high = seeds.get("high_signal", [])
    semantic_medium = seeds.get("medium_signal", [])
    semantic_low = seeds.get("low_signal", [])

    # ---- Sources ----
    src = raw.get("sources", {})
    gh = src.get("github", {})
    hf = src.get("huggingface", {})
    sources = SourceConfig(
        github_queries=gh.get("queries", []),
        github_max_results=gh.get("max_results", 10),
        github_min_stars=gh.get("min_stars", 0),
        hf_queries=hf.get("queries", []),
        hf_max_results=hf.get("max_results", 5),
        rss_feeds=src.get("rss_feeds", []),
    )

    # ---- Red Team ----
    rt = raw.get("red_team", {})
    red_team_hypotheses = rt.get("counter_hypotheses", [])
    red_team_sources = rt.get("counter_sources", [])

    # ---- Obsidian ----
    obs = raw.get("obsidian", {})
    obsidian = ObsidianConfig(
        link_threshold=obs.get("link_threshold", 0.3),
        tags=obs.get("tags", ["#vera"]),
    )

    # ---- Verdict Thresholds ----
    verdicts = [
        VerdictThreshold(
            max=v["max"],
            label=v["label"],
            color=v["color"],
        )
        for v in raw.get("verdict_thresholds", [
            {"max": 0.25, "label": "No significant evidence", "color": "green"},
            {"max": 0.50, "label": "Weak signal", "color": "yellow"},
            {"max": 0.75, "label": "Moderate evidence", "color": "orange"},
            {"max": 1.00, "label": "Strong evidence", "color": "red"},
        ])
    ]

    return DomainOntology(
        domain=domain,
        version=version,
        description=description,
        bayesian=bayesian,
        entities=entities,
        document_types=document_types,
        semantic_seeds_high=semantic_high,
        semantic_seeds_medium=semantic_medium,
        semantic_seeds_low=semantic_low,
        sources=sources,
        red_team_hypotheses=red_team_hypotheses,
        red_team_sources=red_team_sources,
        verdict_thresholds=verdicts,
        obsidian=obsidian,
    )
