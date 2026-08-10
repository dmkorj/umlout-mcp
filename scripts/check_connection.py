#!/usr/bin/env python3
"""Check that the Umlout MCP server is reachable and your API key works.

Run this before opening an issue — it distinguishes "the service is down" from
"my key is wrong" from "something between me and the server is blocking SSE",
which are three very different problems.

    python3 scripts/check_connection.py --api-key YOUR_API_KEY

The key may also come from the UMLOUT_API_KEY environment variable. Standard
library only — nothing to install.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://www.umlout.com/mcp/sse"
TIMEOUT = 15

OK, FAIL, WARN = "  ok  ", " fail ", " warn "


def report(status: str, label: str, detail: str = "") -> None:
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))


def check_health(base: str) -> bool:
    """GET /mcp/health — unauthenticated, so this isolates reachability."""
    url = base.rsplit("/sse", 1)[0] + "/health"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as exc:
        report(FAIL, "service reachable", f"{url} returned HTTP {exc.code}")
        return False
    except Exception as exc:  # noqa: BLE001 — any transport failure is the same answer here
        report(FAIL, "service reachable", f"{url}: {exc}")
        return False

    if body.get("status") == "ok":
        report(OK, "service reachable", url)
        return True
    report(WARN, "service reachable", f"unexpected body: {body!r}")
    return True


def check_auth(url: str, api_key: str) -> bool:
    """Open the SSE stream far enough to learn whether the key was accepted.

    A valid key yields 200 and an event stream that stays open, so read one
    chunk and hang up rather than waiting for an end that never comes.
    """
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "text/event-stream"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ctype = resp.headers.get("Content-Type", "")
            resp.read(1)  # first byte proves the stream opened, then we stop
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            report(FAIL, "API key accepted", f"HTTP {exc.code} — key is wrong, revoked, or malformed")
        elif exc.code == 429:
            report(WARN, "API key accepted", "HTTP 429 — key is valid but you are rate limited")
            return True
        else:
            report(FAIL, "API key accepted", f"HTTP {exc.code}")
        return False
    except TimeoutError:
        report(FAIL, "API key accepted", "timed out waiting for the stream — a proxy may be buffering SSE")
        return False
    except Exception as exc:  # noqa: BLE001
        report(FAIL, "API key accepted", str(exc))
        return False

    if "text/event-stream" not in ctype:
        report(WARN, "API key accepted", f"stream opened but Content-Type is {ctype!r}")
        return True

    report(OK, "API key accepted", "SSE stream opened")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-key", default=os.environ.get("UMLOUT_API_KEY"),
                        help="Umlout API key (default: $UMLOUT_API_KEY)")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"SSE endpoint (default: {DEFAULT_URL})")
    args = parser.parse_args()

    print(f"Checking {args.url}\n")

    healthy = check_health(args.url)

    if not args.api_key:
        report(WARN, "API key accepted", "no key given — pass --api-key or set UMLOUT_API_KEY")
        print("\nReachability checked; key not tested.")
        return 0 if healthy else 1

    authed = check_auth(args.url, args.api_key)

    print()
    if healthy and authed:
        print("All good. Point your MCP client at this URL — see examples/ in this repo.")
        return 0
    print("Something is off. See docs/troubleshooting.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
