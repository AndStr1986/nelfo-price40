"""Tests for the AdditionalInfoLineRecord model (VX/PX post type).

Covers:
- Construction from a raw NELFO line via from_line
- Round-trip serialization via to_line
"""

from nelfo_price40 import AdditionalInfoLineRecord, PostType

from conftest import cast_and_split

VX_SAMPLE = "VX;BILDE;http://www.elektroskandia.no/image/products/1221102.gif"


def test_additional_info_creation():
    """A valid VX line is parsed into an AdditionalInfoLineRecord with correct field values."""
    line = AdditionalInfoLineRecord.from_line(cast_and_split(VX_SAMPLE))
    assert line.post_type == PostType.LINJE_VARE_TILLEGSINFO
    assert line.feltid == "BILDE"
    assert line.verdi == "http://www.elektroskandia.no/image/products/1221102.gif"


def test_additional_info_to_line_round_trip():
    """Serializing a parsed additional info line back to text reproduces the original line."""
    line = AdditionalInfoLineRecord.from_line(cast_and_split(VX_SAMPLE))
    assert line.to_line() == VX_SAMPLE
