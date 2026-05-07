#!/usr/bin/env python3
"""
IrsanAI-VERA — Structure Organizer
vera_organize.py

Bringt Ordnung ins Repository-Root:
- Verschiebt lokale Tools in .tools/
- Verschiebt Patch-Dateien in .tools/patches/
- Zeigt was aufgeräumt wurde

Usage: python vera_organize.py
"""

import shutil
import sys
from pathlib import Path


def find_root() -> Path:
    c = Path.cwd()
    for candidate in [c] + list(c.parents):
        if (candidate / "vera.py").exists():
            return candidate
    return c


def main():
    root = find_root()
    print(f"\n  IrsanAI-VERA Structure Organizer")
    print(f"  Root: {root}\n")

    # Create .tools directory
    tools_dir = root / ".tools"
    patches_dir = tools_dir / "patches"
    reports_dir = tools_dir / "reports"

    for d in [tools_dir, patches_dir, reports_dir]:
        d.mkdir(exist_ok=True)

    moved = []

    # Move local toolchain scripts
    tool_scripts = [
        "irsanai_preflight.py",
        "irsanai_patchbot.py",
        "irsanai_patchbot_status.py",
        "irsanai_resonance_reporter.py",
    ]
    for script in tool_scripts:
        src = root / script
        if src.exists():
            dst = tools_dir / script
            shutil.move(str(src), str(dst))
            moved.append(f"  ✅ {script} → .tools/{script}")

    # Move patch files
    for patch in root.glob("patch_*.txt"):
        dst = patches_dir / patch.name
        shutil.move(str(patch), str(dst))
        moved.append(f"  ✅ {patch.name} → .tools/patches/{patch.name}")

    # Move generated reports from root
    for report in list(root.glob("resonance_report_*.md")) + \
                  list(root.glob("irsanai_preflight_*.md")) + \
                  list(root.glob("patchbot_status_*.md")):
        dst = reports_dir / report.name
        shutil.move(str(report), str(dst))
        moved.append(f"  ✅ {report.name} → .tools/reports/")

    # Create .tools/README.md
    tools_readme = tools_dir / "README.md"
    tools_readme.write_text("""# IrsanAI Local Toolchain

This folder contains local-only tools that bridge Claude (online LLM) and your local environment.

**Never committed to GitHub** — protected by `.gitignore`.

## Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `irsanai_preflight.py` | Full system scan for Claude | `python .tools/irsanai_preflight.py` |
| `irsanai_patchbot.py` | Apply VERA_PATCH instructions | `python .tools/irsanai_patchbot.py patch.txt` |
| `irsanai_patchbot_status.py` | LLM-ready status snapshot | `python .tools/irsanai_patchbot_status.py` |
| `irsanai_resonance_reporter.py` | IST/SOLL validator | `python .tools/irsanai_resonance_reporter.py` |

## Subfolders

- `patches/` — All VERA_PATCH files
- `reports/` — Generated preflight and resonance reports
""", encoding="utf-8")

    if moved:
        print("  Moved:")
        for m in moved:
            print(m)
    else:
        print("  Nothing to move — already organized.")

    print(f"\n  ✅ Done. Run tools from project root:")
    print(f"     python .tools/irsanai_preflight.py")
    print(f"     python .tools/irsanai_patchbot.py .tools/patches/patch_001.txt\n")


if __name__ == "__main__":
    main()
