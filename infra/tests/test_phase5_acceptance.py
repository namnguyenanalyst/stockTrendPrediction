"""Regression tests that acceptance cannot silently substitute its reference server."""

import subprocess
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("arguments", [
    ["--target", "http://127.0.0.1:1"],
    ["--target", "http://127.0.0.1:1", "--force-mock"],
])
def test_explicit_live_target_never_falls_back_to_mock(arguments):
    result = subprocess.run([sys.executable, str(ROOT / "tests/e2e/run_e2e.py"),
        *arguments, "-k", "__not_a_test__"], capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "IN-PROCESS CONTRACT REFERENCE" not in result.stdout
