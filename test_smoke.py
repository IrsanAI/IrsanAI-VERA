"""
IrsanAI-VERA — Smoke Tests
tests/test_smoke.py

Basic sanity checks that verify core system integrity.
These run on every push via GitHub Actions.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def test_bayesian_updater_importable():
    from core.bayesian.updater import BayesianBeliefUpdater, Evidence
    assert BayesianBeliefUpdater is not None
    assert Evidence is not None


def test_bayesian_updater_basic():
    from core.bayesian.updater import BayesianBeliefUpdater, Evidence
    import datetime, tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        updater = BayesianBeliefUpdater(
            prior=0.1,
            hypothesis_name="Test",
            data_dir=Path(tmpdir),
        )
        assert updater.belief == 0.1

        ev = Evidence(
            id="TEST-001",
            source_url="https://example.com",
            source_type="test",
            source_trust_weight=0.5,
            retrieval_method="test",
            retrieved_at=datetime.datetime.now().isoformat(),
            semantic_score=0.5,
            supports_hypothesis=True,
            summary="Test evidence",
        )
        new_belief = updater.update(ev)
        assert new_belief > 0.1, "Pro evidence must raise belief"
        assert 0.0 < new_belief < 1.0, "Belief must never reach 0 or 1"


def test_red_team_lowers_belief():
    from core.bayesian.updater import BayesianBeliefUpdater, Evidence
    import datetime, tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        updater = BayesianBeliefUpdater(
            prior=0.5,
            hypothesis_name="Test",
            data_dir=Path(tmpdir),
        )
        ev_counter = Evidence(
            id="TEST-002",
            source_url="https://example.com/counter",
            source_type="test",
            source_trust_weight=0.5,
            retrieval_method="test",
            retrieved_at=datetime.datetime.now().isoformat(),
            semantic_score=0.5,
            supports_hypothesis=False,  # Red Team
            summary="Counter evidence",
        )
        new_belief = updater.update(ev_counter)
        assert new_belief < 0.5, "Counter evidence must lower belief"


def test_ontology_loader():
    from core.ontology_loader import load_ontology
    ontology_path = ROOT / "ontologies" / "uap.yaml"
    if not ontology_path.exists():
        return  # Skip if no ontology
    ontology = load_ontology(ontology_path)
    assert ontology.domain != ""
    assert ontology.bayesian.prior_tech_coverup > 0
    assert ontology.bayesian.prior_tech_coverup < 1


def test_no_hardcoded_probs_in_bayesian_core():
    updater_path = ROOT / "core" / "bayesian" / "updater.py"
    assert updater_path.exists()
    content = updater_path.read_text(encoding="utf-8")
    antipatterns = ["= 0.81", "= 0.78", "= 0.65", "prob_tech_coverup = 0."]
    for pattern in antipatterns:
        assert pattern not in content, f"Hardcoded probability found: {pattern}"


def test_red_team_has_adversarial_flag():
    rt_path = ROOT / "agents" / "red_team.py"
    assert rt_path.exists()
    content = rt_path.read_text(encoding="utf-8")
    assert "supports_hypothesis=False" in content, \
        "Red Team must set supports_hypothesis=False"


def test_manifest_exists():
    assert (ROOT / "VERA_MANIFEST.md").exists()


def test_vision_exists():
    assert (ROOT / "VISION.md").exists()
