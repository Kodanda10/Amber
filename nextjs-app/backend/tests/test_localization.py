
from datetime import datetime
import pytest

# This import will fail initially, which is expected for TDD
from utils import format_date_in_hindi

def test_hindi_date_formatting_L10N_001():
    """
    Tests the Hindi date formatting utility for task L10N-001.
    It should format a given date into a Devanagari script string.
    """
    test_date = datetime(2025, 10, 4)
    expected_output = "०४ अक्तूबर २०२५"
    
    # This will fail until the function is implemented correctly
    assert format_date_in_hindi(test_date) == expected_output
