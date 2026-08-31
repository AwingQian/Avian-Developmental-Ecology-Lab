"""
Fetch the 10 most recent works from an ORCID record and write them to
publications.json, which the website loads at runtime.

Why ORCID instead of Google Scholar / ResearchGate:
- Google Scholar and ResearchGate have no official public API and both
  actively block/rate-limit automated scraping (ResearchGate especially,
  including from cloud/CI IP ranges like GitHub Actions).
- ORCID provides a free, official, documented public API intended for
  exactly this kind of programmatic access.

Setup (one-time, free, instant self-service):
    1. Sign in at https://orcid.org
    2. Click your name (top right) -> Developer Tools
       (verify your email if prompted)
    3. Register a public API client -> you'll get a Client ID and Client
       Secret
    4. Set them as environment variables (or GitHub Actions secrets):
       ORCID_CLIENT_ID, ORCID_CLIENT_SECRET

Usage (manual):
    pip install requests
    export ORCID_CLIENT_ID=xxxx
    export ORCID_CLIENT_SECRET=xxxx
    python scripts/fetch_orcid.py

This also runs automatically every ~5 days via
.github/workflows/update-publications.yml
"""
import json
import os
import time
from datetime import datetime, timezone

import requests

ORCID_ID = "0000-0001-5389-4157"
CLIENT_ID = os.environ.get("ORCID_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET")
TOKEN_URL = "https://orcid.org/oauth/token"
API_BASE = "https://pub.orcid.org/v3.0"
OUTPUT_PATH = "publications.json"
MAX_PUBS = 10


def get_token() -> str:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "/read-public",
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_works_summary(token: str) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{ORCID_ID}/works", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def year_of_group(group: dict) -> int:
    try:
        summary = group.get("work-summary", [{}])[0]
        date = summary.get("publication-date") or {}
        year = date.get("year") or {}
        return int(year.get("value", 0))
    except (TypeError, ValueError):
        return 0


def get_work_detail(token: str, put_code) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{ORCID_ID}/work/{put_code}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_url(node: dict) -> str:
    ext_ids = ((node or {}).get("external-ids") or {}).get("external-id") or []
    for e in ext_ids:
        if e.get("external-id-type") == "doi" and e.get("external-id-value"):
            return f"https://doi.org/{e['external-id-value']}"
    for e in ext_ids:
        url = e.get("external-id-url") or {}
        if url.get("value"):
            return url["value"]
    url_node = (node or {}).get("url") or {}
    return url_node.get("value", "")


def extract_authors(detail: dict) -> str:
    contributors = ((detail.get("contributors") or {}).get("contributor")) or []
    names = []
    for c in contributors:
        name = (c.get("credit-name") or {}).get("value")
        if name:
            names.append(name)
    return ", ".join(names)


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SystemExit(
            "Missing ORCID_CLIENT_ID / ORCID_CLIENT_SECRET environment variables. "
            "See the setup instructions at the top of this file."
        )

    token = get_token()
    works_data = get_works_summary(token)
    groups = sorted(works_data.get("group", []), key=year_of_group, reverse=True)

    results = []
    for group in groups[:MAX_PUBS]:
        summary = group.get("work-summary", [{}])[0]
        put_code = summary.get("put-code")
        title = ((summary.get("title") or {}).get("title") or {}).get("value", "")
        journal = (summary.get("journal-title") or {}).get("value", "")
        year = ((summary.get("publication-date") or {}).get("year") or {}).get("value", "")

        detail = get_work_detail(token, put_code) if put_code else {}
        url = extract_url(detail) or extract_url(summary)
        authors = extract_authors(detail)

        results.append({
            "year": year,
            "authors": authors,  # may be empty if ORCID record has no contributor list
            "title": title,
            "venue": journal,
            "url": url,
        })
        time.sleep(0.5)

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source": f"https://orcid.org/{ORCID_ID}",
        "publications": results,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(results)} publications to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
