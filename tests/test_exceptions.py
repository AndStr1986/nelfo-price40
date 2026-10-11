"""Tests for the exception classes' structured data (not just their message
text) - RecordLineParsningError, DecoderError, DuplicateRecord, StrayRecord
all carry attributes consumers can inspect directly instead of parsing the
formatted message string."""

from pydantic import ValidationError
from nelfo_price40 import (
    RecordLineParsningError,
    DuplicateRecord,
    StrayRecord,
    ProductLineRecord,
    AlternativeLineRecord,
)
from nelfo_price40.decoders import DecoderChain
from nelfo_price40.exceptions import DecoderError


def test_record_line_parsning_error_exposes_field_details():
    """RecordLineParsningError exposes which field failed, why, and the
    bad value - pulled from the ValidationError's own .title rather than
    being passed in separately."""
    try:
        ProductLineRecord.model_validate({"post_type": "VL", "vare_mrk": "1.."})
    except ValidationError as e:
        err = RecordLineParsningError(original=e, line_number=7)

    assert err.name == "ProductLineRecord"
    assert err.field == "vare_mrk"
    assert err.bad_value == "1.."
    assert "7" in str(err)


def test_duplicate_record_message_includes_model_and_line():
    err = DuplicateRecord(
        model=ProductLineRecord, line_number=42, line_content="VL;1;123;..."
    )
    assert err.model is ProductLineRecord
    assert "42" in str(err)
    assert "ProductLineRecord" in str(err)


def test_stray_record_message_includes_model_and_line():
    err = StrayRecord(
        model=AlternativeLineRecord, line_number=3, line_content="VA;1;123;E;"
    )
    assert "3" in str(err)
    assert "AlternativeLineRecord" in str(err)


def test_decoder_error_computes_line_and_position():
    """DecoderError computes line_number/position_in_line from the byte
    offset UnicodeDecodeError reports, not just the raw offset into the
    whole file."""
    data = b"VH;first;line\nVL;R\xd8D;second;line"
    try:
        DecoderChain().decode(data)
    except DecoderError as e:
        assert e.line_number == 2
        assert e.position_in_line == 3
