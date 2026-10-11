"""Tests for the HeaderLineRecord model (VH/PH post type).

Covers:
- Construction from a raw NELFO line via from_line
- Optional field defaults
- Round-trip serialization via to_line
"""

from nelfo_price40 import HeaderLineRecord, PostType
from conftest import cast_and_split

VH_SAMPLE = "VH;EFONELFO;4.0;NO979692900MVA;;;20081209;;NOK;;Onninen AS;Postboks 70;;1483;SKYTTA;NO"


def test_header_creation():
    """A valid VH line is parsed into a HeaderLineRecord with correct field values."""
    header = HeaderLineRecord.from_line(cast_and_split(VH_SAMPLE))
    assert header.post_type == PostType.HODE_VAREPOST
    assert header.selgers_id == "NO979692900MVA"
    assert header.s_firma_navn == "Onninen AS"
    assert header.s_post_nr == "1483"
    assert header.s_post_sted == "SKYTTA"


def test_header_optional_fields_default_to_none():
    """Empty fields in the raw line (e.g. kjopers_id, til_dato) become None."""
    header = HeaderLineRecord.from_line(cast_and_split(VH_SAMPLE))
    assert header.kjopers_id is None
    assert header.til_dato is None


def test_header_to_line_round_trip():
    """Serializing a parsed header back to text reproduces the original line."""
    header = HeaderLineRecord.from_line(cast_and_split(VH_SAMPLE))
    assert header.to_line() == VH_SAMPLE
