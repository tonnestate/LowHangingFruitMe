"""Internal subprocess-only worker entry point; never exposed as HTTP."""
from __future__ import annotations
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys

def main() -> int:
    if len(sys.argv) != 2:
        return 2
    from .documents import extract_pdf
    try:
        with redirect_stdout(sys.stderr):
            result = extract_pdf(Path(sys.argv[1]))
        sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",",":")))
        return 0
    except Exception:
        return 2

if __name__ == "__main__":
    sys.exit(main())
