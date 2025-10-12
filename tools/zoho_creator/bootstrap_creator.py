import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple

import requests

DC_DOMAIN_MAP = {
    "us": "com",
    "eu": "eu",
    "in": "in",
    "au": "com.au",
    "jp": "jp",
    "ca": "com.ca"
}

def creator_base(dc: str) -> str:
    tld = DC_DOMAIN_MAP.get(dc.lower(), "com")
    return f"https://creator.zoho.{tld}/api/v2"

def accounts_base(dc: str) -> str:
    tld = DC_DOMAIN_MAP.get(dc.lower(), "com")
    return f"https://accounts.zoho.{tld}"

def read_env(k: str, required: bool = True, default: str = "") -> str:
    v = os.getenv(k, default).strip()
    if required and not v:
        raise RuntimeError(f"Missing env var: {k}")
    return v

def get_access_token(dc: str) -> Tuple[str, int]:
    token_url = f"{accounts_base(dc)}/oauth/v2/token"
    payload = {
        "refresh_token": read_env("ZOHO_REFRESH_TOKEN"),
        "client_id": read_env("ZOHO_CLIENT_ID"),
        "client_secret": read_env("ZOHO_CLIENT_SECRET"),
        "grant_type": "refresh_token",
    }
    r = requests.post(token_url, data=payload, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {r.status_code} {r.text}")
    data = r.json()
    return data["access_token"], int(data.get("expires_in", 3600))

def h(token: str) -> Dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"}

def ensure_app(base: str, owner: str, app_name: str, app_link_name: str, token: str, dry_run: bool) -> None:
    get_url = f"{base}/{owner}/apps/{app_link_name}"
    r = requests.get(get_url, headers=h(token), timeout=30)
    if r.status_code == 200:
        print(f"App exists: {app_link_name}")
        return
    if dry_run:
        print(f"[dry-run] Would create app: name={app_name}, link_name={app_link_name}")
        return
    create_url = f"{base}/{owner}/apps"
    payload = {"name": app_name, "link_name": app_link_name}
    r = requests.post(create_url, headers=h(token), data=json.dumps(payload), timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Create app failed: {r.status_code} {r.text}")
    print(f"Created app: {app_link_name}")

def upsert_form(base: str, owner: str, app_link_name: str, form_blueprint: Dict[str, Any], token: str, dry_run: bool) -> None:
    form_link_name = form_blueprint["name"]
    get_url = f"{base}/{owner}/{app_link_name}/forms/{form_link_name}"
    r = requests.get(get_url, headers=h(token), timeout=30)
    exists = r.status_code == 200
    if dry_run:
        print(f"[dry-run] Would {'update' if exists else 'create'} form {form_link_name}")
        return
    if exists:
        put_url = f"{base}/{owner}/{app_link_name}/forms/{form_link_name}"
        r = requests.put(put_url, headers=h(token), data=json.dumps(form_blueprint), timeout=90)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Update form {form_link_name} failed: {r.status_code} {r.text}")
        print(f"Updated form: {form_link_name}")
    else:
        post_url = f"{base}/{owner}/{app_link_name}/forms"
        r = requests.post(post_url, headers=h(token), data=json.dumps(form_blueprint), timeout=90)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Create form {form_link_name} failed: {r.status_code} {r.text}")
        print(f"Created form: {form_link_name}")

def upsert_page(base: str, owner: str, app_link_name: str, page_blueprint: Dict[str, Any], token: str, dry_run: bool) -> None:
    page_link_name = page_blueprint["name"]
    get_url = f"{base}/{owner}/{app_link_name}/pages/{page_link_name}"
    r = requests.get(get_url, headers=h(token), timeout=30)
    exists = r.status_code == 200
    if dry_run:
        print(f"[dry-run] Would {'update' if exists else 'create'} page {page_link_name}")
        return
    if exists:
        put_url = f"{base}/{owner}/{app_link_name}/pages/{page_link_name}"
        r = requests.put(put_url, headers=h(token), data=json.dumps(page_blueprint), timeout=60)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Update page {page_link_name} failed: {r.status_code} {r.text}")
        print(f"Updated page: {page_link_name}")
    else:
        post_url = f"{base}/{owner}/{app_link_name}/pages"
        r = requests.post(post_url, headers=h(token), data=json.dumps(page_blueprint), timeout=60)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Create page {page_link_name} failed: {r.status_code} {r.text}")
        print(f"Created page: {page_link_name}")

def load_blueprint(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Zoho Creator app (idempotent).")
    parser.add_argument("--owner", required=False, default=os.getenv("ZOHO_OWNER", "me"))
    parser.add_argument("--app-name", required=False, default=os.getenv("ZOHO_APP_NAME", "Amber-Experimental"))
    parser.add_argument("--app-link-name", required=False, default=os.getenv("ZOHO_APP_LINK_NAME", "amber_experimental"))
    parser.add_argument("--dc", required=False, default=os.getenv("ZOHO_DC", "us"))
    parser.add_argument("--blueprints-dir", required=False, default=str(Path(__file__).parent / "blueprints"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base = creator_base(args.dc)
    token, _ = get_access_token(args.dc)

    ensure_app(base, args.owner, args.app_name, args.app_link_name, token, args.dry_run)

    bp_dir = Path(args.blueprints_dir)
    forms = ["leaders.form.json", "posts.form.json"]
    for fname in forms:
        upsert_form(base, args.owner, args.app_link_name, load_blueprint(bp_dir / fname), token, args.dry_run)

    upsert_page(base, args.owner, args.app_link_name, load_blueprint(bp_dir / "dashboard.page.json"), token, args.dry_run)

    print("Bootstrap complete.")
    
    # Print the expected Creator app URL
    dc_tld = DC_DOMAIN_MAP.get(args.dc.lower(), "com")
    app_url = f"https://creator.zoho.{dc_tld}/{args.owner}/{args.app_link_name}/"
    print(f"\nCreator app URL: {app_url}")

if __name__ == "__main__":
    main()
