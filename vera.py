"""
IrsanAI-VERA — Veridical Evidence Reasoning Architecture
Entry point: python vera.py --ontology ontologies/uap.yaml
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="IrsanAI-VERA: Veridical Evidence Reasoning Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vera.py --ontology ontologies/uap.yaml
  python vera.py --ontology ontologies/uap.yaml --cycles 3
  python vera.py --list-ontologies
        """
    )
    parser.add_argument("--ontology", "-o", type=Path, help="Domain ontology YAML")
    parser.add_argument("--cycles", "-c", type=int, default=1, help="Investigation cycles (default: 1)")
    parser.add_argument("--vault", type=Path, default=Path("vault"), help="Obsidian vault path")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Data directory")
    parser.add_argument("--no-obsidian", action="store_true", help="Skip Obsidian export")
    parser.add_argument("--github-token", type=str, default=None, help="GitHub API token (optional)")
    parser.add_argument("--list-ontologies", action="store_true", help="List available ontologies")
    parser.add_argument("--version", "-v", action="version", version="IrsanAI-VERA 0.2.0")

    args = parser.parse_args()

    if args.list_ontologies:
        files = list(Path("ontologies").glob("*.yaml"))
        print("\nAvailable ontologies:")
        for f in files:
            print(f"  {f}")
        sys.exit(0)

    if not args.ontology:
        parser.print_help()
        print("\n⚠️  Specify an ontology: --ontology ontologies/uap.yaml")
        sys.exit(1)

    if not args.ontology.exists():
        print(f"❌ Ontology not found: {args.ontology}")
        sys.exit(1)

    try:
        import requests
        import yaml
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install requests pyyaml")
        sys.exit(1)

    from core.ontology_loader import load_ontology
    from core.investigation_cycle import InvestigationCycle

    ontology = load_ontology(args.ontology)

    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("ℹ️  No GitHub token set. Rate limit: 10 req/min.")
        print("   Set via: --github-token <token>  or  GITHUB_TOKEN env var\n")

    for cycle_num in range(1, args.cycles + 1):
        if args.cycles > 1:
            print(f"\n── Cycle {cycle_num}/{args.cycles} ──")

        cycle = InvestigationCycle(
            ontology=ontology,
            data_dir=args.data_dir,
            vault_dir=args.vault,
            github_token=github_token,
            skip_obsidian=args.no_obsidian,
        )
        cycle.run()

    print("\n✅ VERA investigation complete.")
    if not args.no_obsidian:
        print(f"   → Open '{args.vault}' in Obsidian to explore the knowledge graph.")
    print(f"   → Reports saved in '{args.data_dir}'")


if __name__ == "__main__":
    main()
