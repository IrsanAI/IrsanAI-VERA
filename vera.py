"""
IrsanAI-VERA — Veridical Evidence Reasoning Architecture
Entry point: python vera.py --ontology ontologies/uap.yaml
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="IrsanAI-VERA: Veridical Evidence Reasoning Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vera.py --ontology ontologies/uap.yaml
  python vera.py --ontology ontologies/uap.yaml --cycles 10
  python vera.py --list-ontologies
        """
    )
    parser.add_argument(
        "--ontology", "-o",
        type=Path,
        help="Path to domain ontology YAML file"
    )
    parser.add_argument(
        "--cycles", "-c",
        type=int,
        default=1,
        help="Number of investigation cycles to run (default: 1)"
    )
    parser.add_argument(
        "--obsidian-vault",
        type=Path,
        default=Path("vault"),
        help="Path to Obsidian vault output directory (default: ./vault)"
    )
    parser.add_argument(
        "--list-ontologies",
        action="store_true",
        help="List available ontology files"
    )
    parser.add_argument(
        "--no-obsidian",
        action="store_true",
        help="Skip Obsidian vault export"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="IrsanAI-VERA 0.1.0"
    )

    args = parser.parse_args()

    if args.list_ontologies:
        ontology_dir = Path("ontologies")
        files = list(ontology_dir.glob("*.yaml"))
        if files:
            print("\nAvailable ontologies:")
            for f in files:
                print(f"  {f}")
        else:
            print("No ontology files found in ./ontologies/")
        sys.exit(0)

    if not args.ontology:
        parser.print_help()
        print("\n⚠️  No ontology specified. Use --ontology <path> to start.")
        sys.exit(1)

    if not args.ontology.exists():
        print(f"❌ Ontology file not found: {args.ontology}")
        sys.exit(1)

    # Core engine import (will be implemented in core/)
    print(f"""
{'='*60}
  IrsanAI-VERA v0.1.0
  Veridical Evidence Reasoning Architecture
{'='*60}
  Domain   : {args.ontology.stem}
  Cycles   : {args.cycles}
  Vault    : {'disabled' if args.no_obsidian else args.obsidian_vault}
{'='*60}

⚠️  Core engine not yet implemented.
    See ROADMAP.md for development status.
    Run: pip install -e ".[dev]" to set up the environment.
""")


if __name__ == "__main__":
    main()
