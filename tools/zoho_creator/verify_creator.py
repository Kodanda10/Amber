#!/usr/bin/env python3
"""
Verify that the Zoho Creator app has been successfully provisioned.

This script checks:
1. The app exists
2. Required forms (Leaders, Posts) exist
3. Required page (Dashboard) exists

Exit codes:
0 - Success: All components verified
1 - Failure: One or more components missing or verification failed
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Tuple, Optional

import requests

# Import shared functions from bootstrap_creator
sys.path.insert(0, str(Path(__file__).parent))
from bootstrap_creator import (
    creator_base,
    get_access_token,
    h,
    DC_DOMAIN_MAP,
)


def verify_app(base: str, owner: str, app_link_name: str, token: str) -> bool:
    """Verify that the app exists."""
    get_url = f"{base}/{owner}/apps/{app_link_name}"
    try:
        r = requests.get(get_url, headers=h(token), timeout=30)
        if r.status_code == 200:
            print(f"✓ App exists: {app_link_name}")
            return True
        else:
            print(f"✗ App not found: {app_link_name} (status: {r.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error checking app: {e}")
        return False


def verify_form(base: str, owner: str, app_link_name: str, form_name: str, token: str) -> bool:
    """Verify that a form exists."""
    get_url = f"{base}/{owner}/{app_link_name}/forms/{form_name}"
    try:
        r = requests.get(get_url, headers=h(token), timeout=30)
        if r.status_code == 200:
            print(f"✓ Form exists: {form_name}")
            return True
        else:
            print(f"✗ Form not found: {form_name} (status: {r.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error checking form {form_name}: {e}")
        return False


def verify_page(base: str, owner: str, app_link_name: str, page_name: str, token: str) -> bool:
    """Verify that a page exists."""
    get_url = f"{base}/{owner}/{app_link_name}/pages/{page_name}"
    try:
        r = requests.get(get_url, headers=h(token), timeout=30)
        if r.status_code == 200:
            print(f"✓ Page exists: {page_name}")
            return True
        else:
            print(f"✗ Page not found: {page_name} (status: {r.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error checking page {page_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify Zoho Creator app provisioning.")
    parser.add_argument("--owner", required=False, default=os.getenv("ZOHO_OWNER", "me"))
    parser.add_argument("--app-link-name", required=False, default=os.getenv("ZOHO_APP_LINK_NAME", "amber_experimental"))
    parser.add_argument("--dc", required=False, default=os.getenv("ZOHO_DC", "us"))
    args = parser.parse_args()

    print("=" * 60)
    print("Zoho Creator App Provisioning Verification")
    print("=" * 60)
    print()

    try:
        base = creator_base(args.dc)
        token, _ = get_access_token(args.dc)
    except Exception as e:
        print(f"✗ Failed to get access token: {e}")
        print("\nVerification FAILED")
        sys.exit(1)

    results = []

    # Verify app
    print("Checking app...")
    results.append(verify_app(base, args.owner, args.app_link_name, token))
    print()

    # Verify forms
    print("Checking forms...")
    forms = ["Leaders", "Posts"]
    for form_name in forms:
        results.append(verify_form(base, args.owner, args.app_link_name, form_name, token))
    print()

    # Verify page
    print("Checking pages...")
    results.append(verify_page(base, args.owner, args.app_link_name, "Dashboard", token))
    print()

    # Summary
    print("=" * 60)
    if all(results):
        dc_tld = DC_DOMAIN_MAP.get(args.dc.lower(), "com")
        app_url = f"https://creator.zoho.{dc_tld}/{args.owner}/{args.app_link_name}/"
        print("✓ Verification PASSED")
        print(f"\nCreator app URL: {app_url}")
        print("=" * 60)
        sys.exit(0)
    else:
        failed_count = len([r for r in results if not r])
        print(f"✗ Verification FAILED ({failed_count}/{len(results)} checks failed)")
        print("\nRun the bootstrap script to provision the app:")
        print("  python3 tools/zoho_creator/bootstrap_creator.py")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
