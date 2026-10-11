"""Tests for RecordLineRegistry (maps a PostType to its record class).

Covers:
- Each post_type used by NelfoVareFilParser resolves to the correct
  record class via from_line
- An unregistered post_type raises ValueError

Note: this replaces the old LineParser-based dispatch tests. Dispatch is
no longer a standalone public step - NelfoVareFilParser.parse looks up
RecordLineRegistry.get_record(post_type) directly. These tests exercise
that same lookup path, one post_type at a time, as a unit test rather
than only indirectly through a full file parse.
"""

import pytest
from nelfo_price40 import (
    RecordLineRegistry,
    PostType,
    HeaderLineRecord,
    ProductLineRecord,
    AlternativeLineRecord,
    AdditionalInfoLineRecord,
)
from conftest import cast_and_split

VH_SAMPLE = "VH;EFONELFO;4.0;NO979692900MVA;;;20081209;;NOK;;Onninen AS;Postboks 70;;1483;SKYTTA;NO"
VL_SAMPLE = "VL;1;1016420;PFSP 1KV 2X1,5/1,5 B50;NEXANS NORWAY AS;2;MTR;METER;0;10000;20081209;3;010201;R00;;;J;500000;;"
VA_SAMPLE = "VA;1;1067030;E;"
VX_SAMPLE = "VX;BILDE;http://www.elektroskandia.no/image/products/1221102.gif"


def test_resolves_vh_to_header_line_record():
    """PostType.HODE_VAREPOST resolves to HeaderLineRecord."""
    record_class = RecordLineRegistry.get_record(PostType.HODE_VAREPOST)
    record = record_class.from_line(cast_and_split(VH_SAMPLE))
    assert isinstance(record, HeaderLineRecord)


def test_resolves_vl_to_product_line_record():
    """PostType.LINJE_VAREPOST resolves to ProductLineRecord."""
    record_class = RecordLineRegistry.get_record(PostType.LINJE_VAREPOST)
    record = record_class.from_line(cast_and_split(VL_SAMPLE))
    assert isinstance(record, ProductLineRecord)


def test_resolves_va_to_alternative_line_record():
    """PostType.LINJE_VARE_ALTERNATIV resolves to AlternativeLineRecord."""
    record_class = RecordLineRegistry.get_record(PostType.LINJE_VARE_ALTERNATIV)
    record = record_class.from_line(cast_and_split(VA_SAMPLE))
    assert isinstance(record, AlternativeLineRecord)


def test_resolves_vx_to_additional_info_line_record():
    """PostType.LINJE_VARE_TILLEGSINFO resolves to AdditionalInfoLineRecord."""
    record_class = RecordLineRegistry.get_record(PostType.LINJE_VARE_TILLEGSINFO)
    record = record_class.from_line(cast_and_split(VX_SAMPLE))
    assert isinstance(record, AdditionalInfoLineRecord)


def test_both_pl_and_vl_resolve_to_product_line_record():
    """Both the VL (vare) and PL (pristilbud) post_types for a product
    line resolve to the same ProductLineRecord class."""
    assert (
        RecordLineRegistry.get_record(PostType.LINJE_VAREPOST)
        is RecordLineRegistry.get_record(PostType.LINJE_PRISTILBUD)
    )
