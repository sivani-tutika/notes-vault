#!/usr/bin/env python3
"""
Simple runner for .http-style test files.
Usage: python run_http_tests.py [path/to/test_main.http]

It parses blocks separated by lines with '###' and supports requests like in test_main.http:

GET http://127.0.0.1:8000/
Header: value

###

It will print status, response snippet, and perform basic content checks for known endpoints.
"""
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

import requests


def parse_http_file(path: Path) -> List[Dict]:
    raw = path.read_text()
    parts = [p.strip() for p in re.split(r"^\s*###\s*$", raw, flags=re.MULTILINE) if p.strip()]
    requests_list = []
    for part in parts:
        lines = [l.rstrip() for l in part.splitlines() if l.strip()]
        if not lines:
            continue
        # First line: METHOD URL
        first = lines[0]
        m = re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+(\S+)", first, flags=re.I)
        if not m:
            print(f"Skipping unrecognized block:\n{part}\n")
            continue
        method = m.group(1).upper()
        url = m.group(2)
        headers = {}
        body_lines = []
        for ln in lines[1:]:
            if ":" in ln and not ln.startswith("{") and not ln.startswith("["):
                # header line
                k, v = ln.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                body_lines.append(ln)
        body = None
        if body_lines:
            body_text = "\n".join(body_lines).strip()
            # try to parse JSON body if it looks like JSON
            try:
                body = json.loads(body_text)
            except Exception:
                body = body_text
        requests_list.append({"method": method, "url": url, "headers": headers, "body": body})
    return requests_list


# Basic expectations for endpoints in the repo (path -> callable that validates response)
def expect_root(resp: requests.Response) -> Tuple[bool, str]:
    try:
        j = resp.json()
        if j.get("message") == "Hello World":
            return True, "root message OK"
        else:
            return False, f"unexpected json: {j}"
    except Exception:
        return False, "not JSON"


def expect_hello(resp: requests.Response, name: str) -> Tuple[bool, str]:
    try:
        j = resp.json()
        if j.get("message") == f"Hello {name}":
            return True, "hello message OK"
        else:
            return False, f"unexpected json: {j}"
    except Exception:
        return False, "not JSON"


def expect_health(resp: requests.Response) -> Tuple[bool, str]:
    try:
        j = resp.json()
        if j.get("status") == "ok":
            return True, "health OK"
        else:
            return False, f"unexpected json: {j}"
    except Exception:
        return False, "not JSON"


def run_requests(requests_list: List[Dict]):
    all_ok = True
    for i, req in enumerate(requests_list, start=1):
        method = req["method"]
        url = req["url"]
        headers = req.get("headers") or {}
        body = req.get("body")
        print(f"[{i}] {method} {url}")
        try:
            resp = requests.request(method, url, headers=headers, json=body if isinstance(body, dict) else None, data=body if isinstance(body, str) else None, timeout=5)
        except Exception as e:
            print(f"   ERROR: request failed: {e}\n")
            all_ok = False
            continue
        status = resp.status_code
        print(f"   Status: {status}")
        snippet = resp.text[:800].strip()
        print(f"   Response (snippet): {snippet!r}")
        ok = status < 400
        note = ""
        # try to apply expectations for known endpoints
        try:
            path = requests.utils.urlparse(url).path
            if path == "/":
                ok2, note = expect_root(resp)
                ok = ok and ok2
            elif path.startswith("/hello/"):
                name = path.split("/", 2)[-1]
                ok2, note = expect_hello(resp, name)
                ok = ok and ok2
            elif path == "/health":
                ok2, note = expect_health(resp)
                ok = ok and ok2
        except Exception:
            pass

        print(f"   Result: {'PASS' if ok else 'FAIL'}{(' - ' + note) if note else ''}\n")
        if not ok:
            all_ok = False
    return all_ok


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test_main.http")
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(2)
    reqs = parse_http_file(path)
    if not reqs:
        print("No requests parsed from file.")
        sys.exit(2)
    ok = run_requests(reqs)
    if ok:
        print("All tests PASSED")
        sys.exit(0)
    else:
        print("Some tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

