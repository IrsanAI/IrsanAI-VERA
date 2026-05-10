# scripts/validate_manifest.py

import subprocess
import sys
import os

def run_tests():
    result = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0

def check_manifest_exists():
    return os.path.exists("VERA_MANIFEST.md")

def main():
    print("=== VERA Manifest Validation ===")

    checks = {
        "Manifest exists": check_manifest_exists(),
        "Tests pass": run_tests(),
    }

    for name, status in checks.items():
        print(f"{name}: {'PASS' if status else 'FAIL'}")

    if not all(checks.values()):
        print("\n❌ Manifest validation FAILED")
        sys.exit(1)

    print("\n✅ Manifest validation PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()