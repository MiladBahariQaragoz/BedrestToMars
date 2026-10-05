"""Run every test file in this directory.

    python framework/tests/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TESTS = sorted(Path(__file__).resolve().parent.glob("test_*.py"))


def main() -> int:
    failed: list[str] = []
    for test in TESTS:
        result = subprocess.run(
            [sys.executable, str(test)], capture_output=True, text=True
        )
        summary = result.stdout.strip().splitlines()[-1] if result.stdout else "no output"
        status = "ok  " if result.returncode == 0 else "FAIL"
        print(f"{status} {test.name:<32} {summary}")
        if result.returncode != 0:
            failed.append(test.name)
            print(result.stdout)
            print(result.stderr)
    print(f"\n{len(TESTS) - len(failed)}/{len(TESTS)} files passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
