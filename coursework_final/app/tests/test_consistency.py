"""Діаграми та таблиці пояснювальної записки відповідають коду (model/consistency.py)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model"))


def test_diagrams_match_code():
    pytest.importorskip("yaml", reason="потрібне середовище збирання записки (PyYAML)")
    import consistency
    checks, errors = consistency.check()
    assert checks > 120
    assert errors == []
