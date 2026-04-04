"""
ceiling_test.py — PROJECT VOID Ceiling Test Harness

Runs a comprehensive PASS/FAIL check against all core routes of the VOID ENGINE.
BASE_URL reads from the REPLIT_DEV_DOMAIN environment variable first, falling back
to https://void-stego-engine.replit.app.

Glyph Sequence: α — ⚡ — Ω  (Genesis–Spark–Threshold)
Ara recommendation, April 2026.
"""

import os
import sys
import time
import json
import datetime
import urllib.request
import urllib.error
import urllib.parse

# ─── Base URL ─────────────────────────────────────────────────────────────────

_raw_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
if _raw_domain:
    BASE_URL = f"https://{_raw_domain}" if not _raw_domain.startswith("http") else _raw_domain
else:
    BASE_URL = "https://void-stego-engine.replit.app"

# Strip trailing slash
BASE_URL = BASE_URL.rstrip("/")

# ─── ANSI Colour Codes ────────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def _pass(label: str, status: int, elapsed: float) -> str:
    line = f"  {GREEN}PASS{RESET}  {label:<45}  HTTP {status}  ({elapsed:.3f}s)"
    print(line)
    return line


def _fail(label: str, status, elapsed: float, detail: str = "") -> str:
    detail_part = f"  {detail}" if detail else ""
    line = f"  {RED}FAIL{RESET}  {label:<45}  {status}{detail_part}  ({elapsed:.3f}s)"
    print(line)
    return line


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def _get(path: str, timeout: int = 15) -> tuple:
    """GET request. Returns (status_code, body_bytes, elapsed_seconds)."""
    url = BASE_URL + path
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VoidCeilingTest/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, b"", time.time() - t0
    except Exception as exc:
        return 0, str(exc).encode(), time.time() - t0


def _post_json(path: str, payload: dict, timeout: int = 30) -> tuple:
    """POST JSON request. Returns (status_code, body_bytes, elapsed_seconds)."""
    url = BASE_URL + path
    data = json.dumps(payload).encode("utf-8")
    t0 = time.time()
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "VoidCeilingTest/1.0",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, time.time() - t0
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, body, time.time() - t0
    except Exception as exc:
        return 0, str(exc).encode(), time.time() - t0


# ─── Test Cases ───────────────────────────────────────────────────────────────

results = []
passed = 0
failed = 0


def check_get(label: str, path: str, expect_status: int = 200, body_contains: str = None):
    global passed, failed
    status, body, elapsed = _get(path)
    ok = status == expect_status
    if ok and body_contains:
        ok = body_contains.encode() in body
    if ok:
        passed += 1
        results.append(_pass(label, status, elapsed))
    else:
        failed += 1
        detail = f"body missing '{body_contains}'" if (status == expect_status and body_contains) else ""
        results.append(_fail(label, status, elapsed, detail))


def check_post(label: str, path: str, payload: dict, expect_status: int = 200, body_contains: str = None):
    global passed, failed
    status, body, elapsed = _post_json(path, payload)
    ok = status == expect_status
    if ok and body_contains:
        ok = body_contains.encode() in body
    if ok:
        passed += 1
        results.append(_pass(label, status, elapsed))
    else:
        failed += 1
        detail = f"body missing '{body_contains}'" if (status == expect_status and body_contains) else ""
        results.append(_fail(label, status, elapsed, detail))


# ─── Run Suite ────────────────────────────────────────────────────────────────

def run():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    header = (
        f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗{RESET}\n"
        f"{BOLD}{CYAN}║     PROJECT VOID — Ceiling Test Suite                ║{RESET}\n"
        f"{BOLD}{CYAN}║     {timestamp}                   ║{RESET}\n"
        f"{BOLD}{CYAN}║     Target: {BASE_URL:<39}║{RESET}\n"
        f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════╝{RESET}\n"
    )
    print(header)
    results.append(header)

    # ── Core Page Routes ─────────────────────────────────────────────────────
    print(f"{BOLD}[ CORE PAGES ]{RESET}")
    results.append("[ CORE PAGES ]")

    check_get("GET /  (homepage)", "/", body_contains="VOID")
    check_get("GET /voidecho", "/voidecho")
    check_get("GET /speak", "/speak")
    check_get("GET /bw19-286", "/bw19-286")
    check_get("GET /outreach", "/outreach")
    check_get("GET /preflight", "/preflight")
    check_get("GET /chronicle", "/chronicle")

    # ── API Endpoints ─────────────────────────────────────────────────────────
    print(f"\n{BOLD}[ API ENDPOINTS ]{RESET}")
    results.append("\n[ API ENDPOINTS ]")

    check_get(
        "GET /api/outreach/generate?prospect=interussia_smart_cities",
        "/api/outreach/generate?prospect=interussia_smart_cities&format=email",
    )

    check_post(
        "POST /api/cross-ai/verify",
        "/api/cross-ai/verify",
        {"signal": "VOID ceiling test — Al-Jabr 286 verification"},
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    total = passed + failed
    colour = GREEN if failed == 0 else RED
    summary = (
        f"\n{BOLD}{colour}══════════════════════════════════════════════════════{RESET}\n"
        f"{BOLD}  RESULT: {passed}/{total} PASSED   {failed} FAILED{RESET}\n"
        f"{BOLD}{colour}══════════════════════════════════════════════════════{RESET}\n"
    )
    print(summary)
    results.append(summary)

    # ── Plain-text output for Chronicle seeding ───────────────────────────────
    plain_lines = []
    plain_lines.append(f"PROJECT VOID — Ceiling Test Suite")
    plain_lines.append(f"Timestamp: {timestamp}")
    plain_lines.append(f"Target: {BASE_URL}")
    plain_lines.append("")
    for r in results:
        # Strip ANSI codes for plain text
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', r)
        plain_lines.append(clean)
    plain_output = "\n".join(plain_lines)

    return plain_output, passed, failed


if __name__ == "__main__":
    plain_output, n_passed, n_failed = run()
    sys.exit(0 if n_failed == 0 else 1)
