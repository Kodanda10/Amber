"""
CI-002: Backend Coverage Gate Tests
Tests to verify that coverage enforcement works correctly.
"""
from pathlib import Path


def test_coverage_threshold_in_config():
    """
    CI-002: Verify that the coverage threshold is properly configured.
    """
    config_path = Path(__file__).parent.parent / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found"
    
    config_content = config_path.read_text()
    assert "fail_under = 80" in config_content, "Coverage threshold not set to 80%"
    assert "[tool.coverage.report]" in config_content, "Coverage report config not found"


def test_coverage_omits_test_files():
    """
    CI-002: Verify that test files are omitted from coverage.
    """
    config_path = Path(__file__).parent.parent / "pyproject.toml"
    config_content = config_path.read_text()
    
    assert "*/tests/*" in config_content, "Test directory not omitted from coverage"
    assert "*/test_*.py" in config_content, "Test files not omitted from coverage"


def test_pytest_config_exists():
    """
    CI-002: Verify that pytest configuration exists.
    """
    config_path = Path(__file__).parent.parent / "pyproject.toml"
    config_content = config_path.read_text()
    
    assert "[tool.pytest.ini_options]" in config_content, "Pytest config not found"
    assert "testpaths" in config_content, "Test paths not configured"

