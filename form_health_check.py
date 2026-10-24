#!/usr/bin/env python3
"""
form-health-check

A daily check that a landing page still loads, still has its lead form and
still carries its tracking tags. Posts to Slack when something breaks.

Why: a broken form under live ad spend costs money every hour it goes
unnoticed, and nobody notices on a Sunday. This runs from cron and tells you.

Usage:
    python form_health_check.py --config config.json
    python form_health_check.py --config config.json --quiet   (no output when all pages pass)

config.json (see config.example.json):
{
  "slack_webhook": "https://hooks.slack.com/services/...",   optional
  "timeout_seconds": 15,
  "max_load_seconds": 5,
  "pages": [
    {
      "name": "Nonprofit landing page",
      "url": "https://example.com/nonprofits/",
      "form_selector_hints": ["id=\\"lead-form\\"", "name=\\"email\\""],
      "required_tags": ["GTM-", "G-"]
    }
  ]
}

Exit code is 0 when every page passes and 1 otherwise.
"""

import argparse
import json
import sys
import time

import requests

USER_AGENT = "form-health-check/1.0 (+https://github.com)"


def check_page(page: dict, timeout: int, max_load: float) -> dict:
    result = {"name": page.get("name") or page["url"], "url": page["url"], "problems": [], "load_seconds": None}
    started = time.monotonic()
    try:
        response = requests.get(page["url"], headers={"User-Agent": USER_AGENT}, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        result["problems"].append(f"request failed: {exc}")
        return result
    result["load_seconds"] = round(time.monotonic() - started, 2)

    if response.status_code != 200:
        result["problems"].append(f"HTTP {response.status_code}")
    if result["load_seconds"] > max_load:
        result["problems"].append(f"slow: {result['load_seconds']}s (limit {max_load}s)")

    body = response.text or ""
    if "<form" not in body.lower():
        result["problems"].append("no <form> element found")
    for hint in page.get("form_selector_hints", []):
        if hint not in body:
            result["problems"].append(f"form hint not found: {hint}")
    for tag in page.get("required_tags", []):
        if tag not in body:
            result["problems"].append(f"tracking tag not found: {tag}")
    return result


def post_to_slack(webhook: str, text: str) -> None:
    requests.post(webhook, data=json.dumps({"text": text}), headers={"Content-Type": "application/json"}, timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily landing page and form health check.")
    parser.add_argument("--config", required=True, help="Path to config.json")
    parser.add_argument("--quiet", action="store_true", help="Print nothing when every page passes")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)

    timeout = int(config.get("timeout_seconds", 15))
    max_load = float(config.get("max_load_seconds", 5))
    failures = []
    for page in config.get("pages", []):
        result = check_page(page, timeout, max_load)
        status = "PASS" if not result["problems"] else "FAIL"
        if status == "FAIL" or not args.quiet:
            print(f"{status}  {result['name']}  ({result['url']})  load={result['load_seconds']}s")
            for problem in result["problems"]:
                print(f"       - {problem}")
        if result["problems"]:
            failures.append(result)

    if failures and config.get("slack_webhook"):
        lines = ["Landing page health check: FAIL"]
        for failure in failures:
            lines.append(f"- {failure['name']} ({failure['url']})")
            lines += [f"    {p}" for p in failure["problems"]]
        post_to_slack(config["slack_webhook"], "\n".join(lines))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
