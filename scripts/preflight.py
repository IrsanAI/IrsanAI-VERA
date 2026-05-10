# scripts/preflight.py

import sys
import subprocess
import os

def check_virtualenv():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

def check_python_version():
    return sys.version_info >= (3, 10)

def check_required_packages():
    try:
        import pytest
        return True
    except ImportError:
        return False

def main():
    print("=== VERA Preflight Check ===")

    checks = {
        "Python Version OK": check_python_version(),
        "Virtual Environment Active": check_virtualenv(),
        "Pytest Installed": check_required_packages(),
    }

    for name, status in checks.items():
        print(f"{name}: {'PASS' if status else 'FAIL'}")

    if not all(checks.values()):
        print("\nPreflight FAILED. Aborting execution.")
        sys.exit(1)

    print("\nPreflight PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()