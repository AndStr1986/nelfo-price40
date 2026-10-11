"""Tests for the AlternativeLineRecord model (VA/PA post type).

Covers:
- Construction from a raw NELFO line via from_line
- Round-trip serialization via to_line
- Optional salgs_pakning defaults to None
"""

from nelfo_price40 import AlternativeLineRecord, PostType, VareMrk, VaType
from conftest import cast_and_split

VA_SAMPLE = "VA;1;1067030;E;"


def test_alternative_creation():
    """A valid VA line is parsed into an AlternativeLineRecord with correct field values."""
    line = AlternativeLineRecord.from_line(cast_and_split(VA_SAMPLE))
    assert line.post_type == PostType.LINJE_VARE_ALTERNATIV
    assert line.vare_mrk == VareMrk.ELNUMMER
    assert line.vare_nr == "1067030"
    assert line.va_type == VaType.ERSTATNING
    assert line.salgs_pakning is None


def test_alternative_to_line_round_trip():
    """Serializing a parsed alternative line back to text reproduces the original line."""
    line = AlternativeLineRecord.from_line(cast_and_split(VA_SAMPLE))
    assert line.to_line() == VA_SAMPLE
