"""Independent intent examples; these labels never enter runtime evidence."""

import json
from pathlib import Path

import pytest

from ghost_data.authorization import classify

CASES = json.loads((Path(__file__).parent / "fixtures/authorization.json").read_text())


@pytest.mark.parametrize("text,expected", CASES)
def test_supported_requests_and_non_authorizing_language(text, expected):
    assert classify(text) == expected
