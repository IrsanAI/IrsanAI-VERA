#!/usr/bin/env python3
"""
IrsanAI-VERA — GitHub Setup Script
Run this ONCE from your PyCharm project root to initialize git
and prepare the project for GitHub push.

Usage: python setup_github.py
"""

import subprocess
import sys
from pathlib import Path


def run(cmd: str, check: bool = True) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    print("\n" + "=" * 60)
    print("  IrsanAI-VERA — GitHub Setup")
    print("=" * 60 + "\n")

    # Check git
    git_version = run("git --version", check=False)
    if not git_version:
        print("❌ Git not found. Install git first.")
        sys.exit(1)
    print(f"✓ {git_version}")

    # Check if already initialized
    if Path(".git").exists():
        print("✓ Git already initialized")
    else:
        run("git init")
        print("✓ Git initialized")

    # Stage all files
    run("git add .")
    print("✓ Files staged")

    # Initial commit
    run('git commit -m "feat: IrsanAI-VERA v0.1.0 — initial architecture"')
    print("✓ Initial commit created")

    print("""
Next steps:
1. Create a new repository on GitHub:
   → https://github.com/new
   → Name: IrsanAI-VERA
   → Visibility: Public or Private
   → Do NOT initialize with README (we have one)

2. Connect and push:
   git remote add origin https://github.com/IrsanAI/IrsanAI-VERA.git
   git branch -M main
   git push -u origin main

3. Install dependencies:
   pip install -e ".[dev]"

4. Run VERA:
   python vera.py --ontology ontologies/uap.yaml
""")


if __name__ == "__main__":
    main()
