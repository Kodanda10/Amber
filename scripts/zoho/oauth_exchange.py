#!/usr/bin/env python3
"""
Exchange a Zoho OAuth refresh token for a short-lived access token.

Required environment variables:
    ZOHO_CLIENT_ID
    ZOHO_CLIENT_SECRET
    ZOHO_REFRESH_TOKEN

Usage:
    ZOHO_CLIENT_ID=... ZOHO_CLIENT_SECRET=... ZOHO_REFRESH_TOKEN=... python3 scripts/zoho/oauth_exchange.py

On success the script prints the JSON response from Zoho (containing access_token, expires_in, etc.).
On failure it exits with a non-zero status and prints diagnostics to stderr.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ENV_VARS = (
    "ZOHO_CLIENT_ID",
    "ZOHO_CLIENT_SECRET",
    "ZOHO_REFRESH_TOKEN",
)


def _read_env() -> Dict[str, str]:
    missing = []
    values: Dict[str, str] = {}
    for key in ENV_VARS:
        value = os.getenv(key)
        if not value:
            missing.append(key)
        else:
            values[key] = value
    if missing:
        msg = f"Missing required environment variables: {', '.join(missing)}"
        print(msg, file=sys.stderr)
        sys.exit(1)
    return values


def main() -> None:
    env = _read_env()
    payload = urlencode(
        {
            "client_id": env["ZOHO_CLIENT_ID"],
            "client_secret": env["ZOHO_CLIENT_SECRET"],
            "refresh_token": env["ZOHO_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")

    request = Request(
        TOKEN_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
    except HTTPError as err:
        detail = err.read().decode("utf-8", errors="ignore")
        print(
            f"HTTP error {err.code} when requesting token: {detail or err.reason}",
            file=sys.stderr,
        )
        sys.exit(1)
    except URLError as err:
        print(f"Failed to reach Zoho Accounts: {err.reason}", file=sys.stderr)
        sys.exit(1)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print("Unexpected response from Zoho Accounts (not JSON):", file=sys.stderr)
        print(body, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(parsed, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
