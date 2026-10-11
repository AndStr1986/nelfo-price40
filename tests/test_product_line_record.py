"""Tests for the ProductLineRecord model (VL/PL post type).

Covers:
- Construction from a raw NELFO line via from_line
- Round-trip serialization via to_line
- Default empty alternatives/additional_info lists
- Validation failure for an invalid enum value
"""

import pytest
from pydantic import ValidationError
from nelfo_price40 import ProductLineRecord, PostType, VareMrk, MaaleEnhet, LinjeStatus
from conftest import cast_and_split

VL_SAMPLE = "VL;1;1016420;PFSP 1KV 2X1,5/1,5 B50;NEXANS NORWAY AS;2;MTR;METER;0;10000;20081209;3;010201;R00;;;J;500000;;"


def test_product_line_creation():
    """A valid VL line is parsed into a ProductLineRecord with correct field values."""
    line = ProductLineRecord.from_line(cast_and_split(VL_SAMPLE))
    assert line.post_type == PostType.LINJE_VAREPOST
    assert line.vare_mrk == VareMrk.ELNUMMER
    assert line.vare_nr == "1016420"
    assert line.status == LinjeStatus.UTGAAR
    assert line.maale_enhet == MaaleEnhet.METER


def test_product_line_to_line_round_trip():
    """Serializing a parsed product line back to text reproduces the original line."""
    line = ProductLineRecord.from_line(cast_and_split(VL_SAMPLE))
    assert line.to_line() == VL_SAMPLE


def test_product_line_starts_with_empty_children():
    """A freshly parsed product line has no alternatives/additional_info yet -
    those are only attached later by NelfoVareFilParser as VX/VA records
    belonging to it are encountered."""
    line = ProductLineRecord.from_line(cast_and_split(VL_SAMPLE))
    assert line.alternatives == []
    assert line.additional_info == []


def test_product_line_invalid_vare_mrk_raises():
    """An unrecognised vare_mrk value raises a ValidationError.

    Note: from_line does not wrap this into RecordLineParsningError itself -
    that translation happens one layer up, in NelfoVareFilParser.parse,
    where the line number is available. Calling from_line directly (as
    this test does) surfaces the raw pydantic error.
    """
    bad_line = VL_SAMPLE.replace(";1;1016420", ";1..;1016420", 1)
    with pytest.raises(ValidationError):
        ProductLineRecord.from_line(cast_and_split(bad_line))
