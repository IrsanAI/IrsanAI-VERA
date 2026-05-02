"""
IrsanAI-VERA — Veridical Evidence Reasoning Architecture
v0.3.0 — .env support, Obsidian active, improved agents

Usage:
  python vera.py --ontology ontologies/uap.yaml
  python vera.py --ontology ontologies/uap.yaml --cycles 3
  streamlit run dashboard/app.py
"""

import argparse
import os
import sys
from pathlib import Path


def _load_env():
    env_path = Path(".env")
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        description="IrsanAI-VERA: Veridical Evidence Reasoning Architecture"
    )
    parser.add_argument("--ontology", "-o", type=Path, help="Domain ontology YAML file")
    parser.add_argument("--cycles", "-c", type=int, default=1)
    parser.add_argument("--vault", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--no-obsidian", action="store_true")
    parser.add_argument("--github-token", type=str, default=None)
    parser.add_argument("--list-ontologies", action="store_true")
    parser.add_argument("--version", "-v", action="version", version="IrsanAI-VERA 0.3.0")

    args = parser.parse_args()

    if args.list_ontologies:
        for f in Path("ontologies").glob("*.yaml"):
            print(f"  {f}")
        sys.exit(0)

    if not args.ontology:
        parser.print_help()
        print("\n⚠️  python vera.py --ontology ontologies/uap.yaml")
        sys.exit(1)

    if not args.ontology.exists():
        print(f"❌ Not found: {args.ontology}")
        sys.exit(1)

    vault_path = args.vault or Path(os.environ.get("OBSIDIAN_VAULT_PATH", "vault"))
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")

    if not github_token:
        print("ℹ️  No GitHub token. Copy .env.example → .env and add GITHUB_TOKEN\n")
    else:
        print("✓  GitHub token loaded\n")

    try:
        import requests, yaml
    except ImportError as e:
        print(f"❌ pip install requests pyyaml  ({e})")
        sys.exit(1)

    from core.ontology_loader import load_ontology
    from core.investigation_cycle import InvestigationCycle

    ontology = load_ontology(args.ontology)

    for i in range(1, args.cycles + 1):
        if args.cycles > 1:
            print(f"\n── Cycle {i}/{args.cycles} ──")
        InvestigationCycle(
            ontology=ontology,
            data_dir=args.data_dir,
            vault_dir=vault_path,
            github_token=github_token,
            skip_obsidian=args.no_obsidian,
        ).run()

    print("\n✅ VERA complete.")
    if not args.no_obsidian:
        print(f"   Obsidian vault → '{vault_path}'  (open folder in Obsidian)")
    print(f"   Reports        → '{args.data_dir}'")
    print(f"   Dashboard      → streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
