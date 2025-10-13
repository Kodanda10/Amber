"""
Tests for Zoho Creator bootstrap and verification scripts.
"""
import json
import os
from pathlib import Path
from unittest import mock
import pytest

# Set up path to import the modules
import sys
TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from bootstrap_creator import (
    creator_base,
    accounts_base,
    DC_DOMAIN_MAP,
    load_blueprint,
)


def test_creator_base_us():
    """Test creator_base URL for US datacenter."""
    assert creator_base("us") == "https://creator.zoho.com/api/v2"


def test_creator_base_eu():
    """Test creator_base URL for EU datacenter."""
    assert creator_base("eu") == "https://creator.zoho.eu/api/v2"


def test_creator_base_default():
    """Test creator_base URL with unknown DC defaults to .com."""
    assert creator_base("unknown") == "https://creator.zoho.com/api/v2"


def test_accounts_base_us():
    """Test accounts_base URL for US datacenter."""
    assert accounts_base("us") == "https://accounts.zoho.com"


def test_accounts_base_eu():
    """Test accounts_base URL for EU datacenter."""
    assert accounts_base("eu") == "https://accounts.zoho.eu"


def test_dc_domain_map_completeness():
    """Test that all expected datacenters are in the mapping."""
    expected_dcs = ["us", "eu", "in", "au", "jp", "ca"]
    for dc in expected_dcs:
        assert dc in DC_DOMAIN_MAP, f"Missing datacenter: {dc}"


def test_load_blueprint_leaders():
    """Test loading the Leaders form blueprint."""
    blueprint_path = TOOLS_DIR / "blueprints" / "leaders.form.json"
    blueprint = load_blueprint(blueprint_path)
    
    assert blueprint["name"] == "Leaders"
    assert blueprint["display_name"] == "Leaders"
    assert "fields" in blueprint
    assert len(blueprint["fields"]) > 0
    
    # Check for required fields
    field_names = [f["name"] for f in blueprint["fields"]]
    assert "name" in field_names
    assert "party" in field_names
    assert "region" in field_names


def test_load_blueprint_posts():
    """Test loading the Posts form blueprint."""
    blueprint_path = TOOLS_DIR / "blueprints" / "posts.form.json"
    blueprint = load_blueprint(blueprint_path)
    
    assert blueprint["name"] == "Posts"
    assert blueprint["display_name"] == "Posts"
    assert "fields" in blueprint
    
    # Check for required fields
    field_names = [f["name"] for f in blueprint["fields"]]
    assert "platformPostId" in field_names
    assert "leader" in field_names
    assert "platform" in field_names
    assert "text" in field_names


def test_load_blueprint_dashboard():
    """Test loading the Dashboard page blueprint."""
    blueprint_path = TOOLS_DIR / "blueprints" / "dashboard.page.json"
    blueprint = load_blueprint(blueprint_path)
    
    assert blueprint["name"] == "Dashboard"
    assert blueprint["display_name"] == "Dashboard"
    assert blueprint["type"] == "page"
    assert "widgets" in blueprint


@mock.patch.dict(os.environ, {
    "ZOHO_CLIENT_ID": "test_client",
    "ZOHO_CLIENT_SECRET": "test_secret",
    "ZOHO_REFRESH_TOKEN": "test_token"
})
@mock.patch("bootstrap_creator.requests.post")
def test_get_access_token_success(mock_post):
    """Test successful access token retrieval."""
    from bootstrap_creator import get_access_token
    
    # Mock successful response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mock_access_token",
        "expires_in": 3600
    }
    mock_post.return_value = mock_response
    
    token, expires = get_access_token("us")
    
    assert token == "mock_access_token"
    assert expires == 3600
    assert mock_post.called


@mock.patch("bootstrap_creator.requests.get")
def test_ensure_app_exists(mock_get):
    """Test ensure_app when app already exists."""
    from bootstrap_creator import ensure_app
    
    # Mock app exists response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Should not raise an error
    ensure_app("https://creator.zoho.com/api/v2", "owner", "Test App", "test_app", "token", False)
    
    assert mock_get.called


def test_blueprints_directory_exists():
    """Test that blueprints directory exists with required files."""
    blueprints_dir = TOOLS_DIR / "blueprints"
    assert blueprints_dir.exists(), "blueprints directory should exist"
    
    required_files = [
        "leaders.form.json",
        "posts.form.json",
        "dashboard.page.json"
    ]
    
    for filename in required_files:
        filepath = blueprints_dir / filename
        assert filepath.exists(), f"Required blueprint file missing: {filename}"


def test_blueprint_json_validity():
    """Test that all blueprint files contain valid JSON."""
    blueprints_dir = TOOLS_DIR / "blueprints"
    json_files = list(blueprints_dir.glob("*.json"))
    
    assert len(json_files) > 0, "No blueprint JSON files found"
    
    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{json_file.name} should contain a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file.name}: {e}")


@mock.patch("verify_creator.requests.get")
def test_verify_app_success(mock_get):
    """Test verify_app when app exists."""
    from verify_creator import verify_app
    
    # Mock successful response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = verify_app("https://creator.zoho.com/api/v2", "owner", "test_app", "token")
    
    assert result is True
    assert mock_get.called


@mock.patch("verify_creator.requests.get")
def test_verify_app_not_found(mock_get):
    """Test verify_app when app does not exist."""
    from verify_creator import verify_app
    
    # Mock not found response
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    result = verify_app("https://creator.zoho.com/api/v2", "owner", "test_app", "token")
    
    assert result is False
    assert mock_get.called


@mock.patch("verify_creator.requests.get")
def test_verify_form_success(mock_get):
    """Test verify_form when form exists."""
    from verify_creator import verify_form
    
    # Mock successful response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = verify_form("https://creator.zoho.com/api/v2", "owner", "test_app", "Leaders", "token")
    
    assert result is True
    assert mock_get.called


@mock.patch("verify_creator.requests.get")
def test_verify_page_success(mock_get):
    """Test verify_page when page exists."""
    from verify_creator import verify_page
    
    # Mock successful response
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = verify_page("https://creator.zoho.com/api/v2", "owner", "test_app", "Dashboard", "token")
    
    assert result is True
    assert mock_get.called
