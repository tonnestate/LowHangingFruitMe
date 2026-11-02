"""Run a local, read-only synthetic or authorized audit through JSON I/O."""

import argparse
import json
from pathlib import Path
import sys

from .rebate import audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic supplier bonus data audit")
    parser.add_argument("input", type=Path, help="JSON file of rule, transaction and settlement data")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = audit(payload)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"audit rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == "EVIDENCED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
