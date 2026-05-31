"""
IrsanAI-VERA — Complete Fix Script v0.4.1
Run: python vera_fix_all.py

Fixes:
1. Clears VERAMemoryStore (GitHub 0 repos issue)
2. Updates CIP architecture map to reflect implemented modules
3. Verifies interleaving patch is applied
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def fix_memory():
    """Clear VERAMemoryStore so GitHub repos can be found again."""
    cleared = []
    for mem_dir in [ROOT / ".vera_memory", ROOT / ".vera_memory_backup"]:
        if mem_dir.exists():
            shutil.rmtree(mem_dir)
            cleared.append(mem_dir.name)
    if cleared:
        print(f"  ✅ Memory cleared: {', '.join(cleared)}")
    else:
        print("  ℹ️  No memory store found (already clean)")


def fix_cip_architecture():
    """Update CIP architecture map to reflect v0.4.1 implemented modules."""
    cip_path = ROOT / ".tools" / "irsanai_cip_v2.py"
    if not cip_path.exists():
        print("  ⚠️  CIP v2 not found — skipping")
        return

    content = cip_path.read_text(encoding="utf-8")

    replacements = [
        (
            "[📋 MISSING: AutopilotController]",
            "[✅ AutopilotController — enforce_interleaving (Manus.im + LeChat)]",
        ),
        (
            "Architecture v0.4.0",
            "Architecture v0.4.1",
        ),
        (
            "║  [M-001] core/autopilot.py        — Resonance Controller            ║",
            "║  [✅ M-001] core/autopilot.py      — Implemented (Manus.im + LeChat) ║",
        ),
        (
            "║  [M-002] core/memory/chromadb.py  — Cross-session memory            ║",
            "║  [✅ M-002] agents/osint_github.py — VERAMemoryStore integrated      ║",
        ),
        (
            "║  [M-003] agents/nlp_signal.py     — Semantic scoring                ║",
            "║  [✅ M-003] agents/nlp_signal.py   — NLP rescoring active (v1.1)    ║",
        ),
        (
            "║  [M-004] core/graph/knowledge.py  — Cross-session graph             ║",
            "║  [✅ M-004] core/graph/knowledge.py — Implemented (LeChat)          ║",
        ),
        (
            "║  [M-005] api/server.py            — FastAPI backend                 ║",
            "║  [📋 M-005] api/server.py          — FastAPI backend (open)         ║",
        ),
    ]

    changed = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed += 1

    if changed:
        cip_path.write_text(content, encoding="utf-8")
        print(f"  ✅ CIP architecture updated ({changed} changes)")
    else:
        print("  ℹ️  CIP already up to date")


def check_interleaving():
    """Verify interleaving fix is in investigation_cycle.py."""
    cycle_path = ROOT / "core" / "investigation_cycle.py"
    if not cycle_path.exists():
        print("  ⚠️  investigation_cycle.py not found")
        return False

    content = cycle_path.read_text(encoding="utf-8")

    if "zip_longest" in content and "_pro" in content and "_counter" in content:
        print("  ✅ Direct interleaving: ACTIVE")
        return True
    elif "enforce_interleaving" in content:
        print("  ⚠️  Using autopilot.enforce_interleaving — apply patch_018 first")
        return False
    else:
        print("  ❌ No interleaving found!")
        return False


def check_nlp_threshold():
    """Verify NLP threshold is 0.20 not 0.65."""
    nlp_path = ROOT / "agents" / "nlp_signal.py"
    if not nlp_path.exists():
        print("  ⚠️  nlp_signal.py not found")
        return

    content = nlp_path.read_text(encoding="utf-8")
    if "threshold: float = 0.20" in content:
        print("  ✅ NLP threshold: 0.20 (correct)")
    elif "threshold: float = 0.65" in content:
        print("  ❌ NLP threshold: 0.65 (too high — change to 0.20)")
    else:
        print("  ⚠️  NLP threshold: unknown")

    if "not ev.supports_hypothesis" in content:
        print("  ✅ Counter-evidence protection: ACTIVE")
    else:
        print("  ❌ Counter-evidence protection: MISSING")


def update_hall():
    """Ensure Hall of Actives has community contributors."""
    hall_path = ROOT / ".tools" / "hall_of_actives.json"
    hall_path.parent.mkdir(exist_ok=True)

    existing = {}
    if hall_path.exists():
        try:
            existing = json.loads(hall_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    contributors = existing.get("contributors", [])
    names = {c["name"] for c in contributors}

    added = []
    if "Manus.im" not in names:
        contributors.append({
            "name": "Manus.im",
            "contribution": "BUG-001 fix — enforce_interleaving via zip_longest",
            "module": "core/autopilot.py",
            "date": "2026-05-16",
            "listed": True,
        })
        added.append("Manus.im")

    if "LeChat (Mistral)" not in names:
        contributors.append({
            "name": "LeChat (Mistral)",
            "contribution": "M-001 Autopilot + M-002 Memory + M-003 NLP implementation",
            "module": "M-001/M-002/M-003",
            "date": "2026-05-16",
            "listed": True,
        })
        added.append("LeChat (Mistral)")

    existing["contributors"] = contributors
    existing["total_contributions"] = len(contributors)
    existing["last_updated"] = "2026-05-29"

    hall_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    if added:
        print(f"  ✅ Hall of Actives: added {', '.join(added)}")
    else:
        print(f"  ℹ️  Hall of Actives: {len(contributors)} contributors already registered")


def main():
    print("\n  IrsanAI-VERA — Fix All v0.4.1")
    print("  " + "=" * 48 + "\n")

    print("  [1/4] Memory Store")
    fix_memory()

    print("\n  [2/4] Interleaving Check")
    check_interleaving()

    print("\n  [3/4] NLP Agent")
    check_nlp_threshold()

    print("\n  [4/4] Hall of Actives + CIP")
    update_hall()
    fix_cip_architecture()

    print("\n  " + "=" * 48)
    print("  Now run:")
    print("  python vera.py --ontology ontologies/uap.yaml --no-obsidian")
    print()


if __name__ == "__main__":
    main()
