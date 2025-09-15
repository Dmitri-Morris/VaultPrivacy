#!/usr/bin/env python3
"""
Basic tests for the VaultPrivacy parser module.
"""

import json
import tempfile
from pathlib import Path
from vaultprivacy.parser import extract_domains


def test_extract_domains_json():
    """Test extracting domains from JSON format."""
    # Create a temporary JSON file
    sample_data = {
        "encrypted": False,
        "folders": [],
        "items": [
            {
                "login": {
                    "uris": [
                        {"uri": "https://example.com"},
                        {"uri": "https://test.org"}
                    ]
                }
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_file = f.name
    
    try:
        domains = extract_domains(temp_file)
        assert "example.com" in domains
        assert "test.org" in domains
        print("✅ JSON parsing test passed")
    finally:
        Path(temp_file).unlink()


def test_extract_domains_empty():
    """Test handling empty vault."""
    sample_data = {
        "encrypted": False,
        "folders": [],
        "items": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_file = f.name
    
    try:
        domains = extract_domains(temp_file)
        assert len(domains) == 0
        print("✅ Empty vault test passed")
    finally:
        Path(temp_file).unlink()


if __name__ == "__main__":
    test_extract_domains_json()
    test_extract_domains_empty()
    print("All tests passed!")
