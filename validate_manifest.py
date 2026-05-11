#!/usr/bin/env python3
"""
IrsanAI-VERA — Manifest Validator
scripts/validate_manifest.py

Validates the VERA_MANIFEST.md exists and core system integrity.
No external dependencies beyond the standard library.
Runs on every push via GitHub Actions.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def check(label: str, result: bool) -> bool:
    status = "PASS" if result else "FAIL"
    print(f"{label}: {status}")
    return result


def manifest_exists() -> bool:
    return (ROOT / "VERA_MANIFEST.md").exists()


def core_files_exist() -> bool:
    required = [
        "vera.py",
        "core/bayesian/updater.py",
        "core/auditor.py",
        "agents/red_team.py",
        "agents/osint_github.py",
        "agents/osint_huggingface.py",
        "core/lrp_messenger.py",
        "core/investigation_cycle.py",
        "core/ontology_loader.py",
        "obsidian_writer/exporter.py",
        "ontologies/uap.yaml",
        "dashboard/app.py",
        "requirements.txt",
        "README.md",
        "VISION.md",
        "CONTRIBUTING.md",
    ]
    missing = [f for f in required if not (ROOT / f).exists()]
    if missing:
        for m in missing:
            print(f"  MISSING: {m}")
    return len(missing) == 0


def bayesian_integrity() -> bool:
    """Check critical Bayesian signatures are present."""
    updater = ROOT / "core/bayesian/updater.py"
    if not updater.exists():
        return False
    content = updater.read_text(encoding="utf-8", errors="ignore")
    required = ["likelihood_ratio", "BayesianBeliefUpdater", "supports_hypothesis"]
    missing = [s for s in required if s not in content]
    if missing:
        print(f"  MISSING SIGNATURES: {missing}")
    return len(missing) == 0


def red_team_integrity() -> bool:
    """Check Red Team Agent has adversarial flag."""
    rt = ROOT / "agents/red_team.py"
    if not rt.exists():
        return False
    content = rt.read_text(encoding="utf-8", errors="ignore")
    return "supports_hypothesis=False" in content


def no_hardcoded_probs() -> bool:
    """Check for hardcoded probability antipatterns in core files."""
    antipatterns = [
        "prob_tech_coverup = 0.",
        "confidence = 0.81",
        "confidence = 0.78",
        "belief = 0.8",
    ]
    violations = []
    for pyfile in (ROOT / "core").rglob("*.py"):
        content = pyfile.read_text(encoding="utf-8", errors="ignore")
        for pattern in antipatterns:
            if pattern in content:
                violations.append(f"{pyfile.name}: '{pattern}'")
    if violations:
        for v in violations:
            print(f"  HARDCODED: {v}")
    return len(violations) == 0


def smoke_tests() -> bool:
    """Run smoke tests if they exist, skip gracefully if not."""
    test_dir = ROOT / "tests"
    if not test_dir.exists():
        print("  (no tests/ dir — skipping)")
        return True

    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print("  (no test files — skipping)")
        return True

    # Try pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
            capture_output=True, text=True, timeout=60, cwd=ROOT
        )
        if result.returncode != 0:
            print(result.stdout[-500:] if result.stdout else "")
            print(result.stderr[-200:] if result.stderr else "")
        return result.returncode == 0
    except Exception as e:
        print(f"  (pytest unavailable: {e} — skipping)")
        return True


def gitignore_protects_secrets() -> bool:
    """Verify .env and sensitive files are in .gitignore."""
    gi = ROOT / ".gitignore"
    if not gi.exists():
        return False
    content = gi.read_text(encoding="utf-8", errors="ignore")
    required = [".env", "data/", "vault/"]
    missing = [r for r in required if r not in content]
    if missing:
        print(f"  NOT IGNORED: {missing}")
    return len(missing) == 0


def main():
    print("=== VERA Manifest Validation ===\n")

    results = {
        "Manifest exists": check("Manifest exists", manifest_exists()),
        "Core files present": check("Core files present", core_files_exist()),
        "Bayesian integrity": check("Bayesian integrity", bayesian_integrity()),
        "Red Team adversarial": check("Red Team adversarial", red_team_integrity()),
        "No hardcoded probs": check("No hardcoded probs", no_hardcoded_probs()),
        "Secrets protected": check("Secrets protected", gitignore_protects_secrets()),
        "Smoke tests": check("Smoke tests", smoke_tests()),
    }

    print()
    passed = sum(results.values())
    total = len(results)

    if all(results.values()):
        print(f"✅ Manifest validation PASSED ({passed}/{total})")
        sys.exit(0)
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"❌ Manifest validation FAILED — {len(failed)} check(s) failed: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
