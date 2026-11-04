"""One-shot low-privilege, network-isolated Docling worker.

Only a root-owned operator sandbox launcher should invoke this entry point.
The worker refuses to parse if its network namespace is not isolated from the
API process or if a non-loopback interface is available.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import re
import resource
import sys


def require_isolated_network() -> None:
    if sys.platform != "linux":
        raise RuntimeError("unsupported document worker platform")
    expected = os.environ.get("LHFM_PARENT_NETNS", "")
    if not re.fullmatch(r"net:\[\d+\]", expected):
        raise RuntimeError("parent namespace attestation missing")
    own = os.readlink("/proc/self/ns/net")
    if own == expected:
        raise RuntimeError("document worker shares the API network namespace")
    interfaces = set(os.listdir("/sys/class/net"))
    if interfaces != {"lo"}:
        raise RuntimeError("document worker has an unexpected network interface")


def restrict_worker_resources() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        require_isolated_network()
        restrict_worker_resources()
        if sys.argv[1] == "--preflight":
            sys.stdout.write('{"sandbox":"NETWORK_ISOLATED"}')
            return 0
        from .documents import extract_pdf
        with redirect_stdout(sys.stderr):
            result = extract_pdf(Path(sys.argv[1]))
        sys.stdout.write(json.dumps(result, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False))
        return 0
    except Exception:
        # Never expose original contract text, parser trace or private paths.
        return 2


if __name__ == "__main__":
    sys.exit(main())
