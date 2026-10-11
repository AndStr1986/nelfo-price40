"""Tests for NelfoVareFilBuilder in isolation - the hierarchy rules
(duplicate header, duplicate vare_nr, stray VX/VA) exercised directly
against hand-built Record instances, with no file decoding or line
splitting involved. Full-file behavior is covered separately in
test_vare_fil_parser.py.
"""

import pytest
from nelfo_price40 import (
    AdditionalInfoLineRecord,
    AlternativeLineRecord,
    DuplicateRecord,
    HeaderLineRecord,
    NelfoVareFilBuilder,
    ProductLineRecord,
    StrayRecord,
)
from conftest import cast_and_split

VH_SAMPLE = "VH;EFONELFO;4.0;NO979692900MVA;;;20081209;;NOK;;Onninen AS;Postboks 70;;1483;SKYTTA;NO"
VL_SAMPLE = "VL;1;1016420;PFSP 1KV 2X1,5/1,5 B50;NEXANS NORWAY AS;2;MTR;METER;0;10000;20081209;3;010201;R00;;;J;500000;;"
VL_SAMPLE_2 = "VL;1;1067030;PFSP 1KV 2X1,5/1,5 B50;NEXANS NORWAY AS;2;MTR;METER;5400;10000;20081209;1;010201;R00;;;J;500000;;"
VA_SAMPLE = "VA;1;1067030;E;"
VX_SAMPLE = "VX;BILDE;http://www.elektroskandia.no/image/products/1221102.gif"


def header() -> HeaderLineRecord:
    return HeaderLineRecord.from_line(cast_and_split(VH_SAMPLE))


def product(sample: str = VL_SAMPLE) -> ProductLineRecord:
    return ProductLineRecord.from_line(cast_and_split(sample))


def alternative() -> AlternativeLineRecord:
    return AlternativeLineRecord.from_line(cast_and_split(VA_SAMPLE))


def additional_info() -> AdditionalInfoLineRecord:
    return AdditionalInfoLineRecord.from_line(cast_and_split(VX_SAMPLE))


def test_build_fails_without_header():
    """build() refuses to produce a NelfoVareFil40 with no header set."""
    builder = NelfoVareFilBuilder()
    builder.add_record(product(), line_number=1, line_content=VL_SAMPLE)

    with pytest.raises(ValueError):
        builder.build()


def test_build_succeeds_with_header_only():
    """A header with zero products is a valid, buildable file."""
    builder = NelfoVareFilBuilder()
    builder.add_record(header(), line_number=1, line_content=VH_SAMPLE)

    nelfo_file = builder.build()

    assert nelfo_file.header.s_firma_navn == "Onninen AS"
    assert nelfo_file.products == []


def test_duplicate_header_raises():
    """A second HeaderLineRecord raises DuplicateRecord."""
    builder = NelfoVareFilBuilder()
    builder.add_record(header(), line_number=1, line_content=VH_SAMPLE)

    with pytest.raises(DuplicateRecord):
        builder.add_record(header(), line_number=5, line_content=VH_SAMPLE)


def test_duplicate_vare_nr_raises():
    """A second ProductLineRecord with the same vare_nr raises DuplicateRecord."""
    builder = NelfoVareFilBuilder()
    builder.add_record(product(), line_number=1, line_content=VL_SAMPLE)

    with pytest.raises(DuplicateRecord):
        builder.add_record(product(), line_number=2, line_content=VL_SAMPLE)


def test_alternative_attaches_to_last_product():
    """An AlternativeLineRecord is appended to the most recently added
    product's .alternatives list."""
    builder = NelfoVareFilBuilder()
    builder.add_record(header(), line_number=1, line_content=VH_SAMPLE)
    builder.add_record(product(), line_number=2, line_content=VL_SAMPLE)
    builder.add_record(alternative(), line_number=3, line_content=VA_SAMPLE)

    nelfo_file = builder.build()

    assert nelfo_file.products[0].alternatives[0].vare_nr == "1067030"


def test_additional_info_attaches_to_last_product():
    """An AdditionalInfoLineRecord is appended to the most recently added
    product's .additional_info list."""
    builder = NelfoVareFilBuilder()
    builder.add_record(header(), line_number=1, line_content=VH_SAMPLE)
    builder.add_record(product(), line_number=2, line_content=VL_SAMPLE)
    builder.add_record(additional_info(), line_number=3, line_content=VX_SAMPLE)

    nelfo_file = builder.build()

    assert nelfo_file.products[0].additional_info[0].feltid == "BILDE"


def test_stray_alternative_before_any_product_raises():
    """An AlternativeLineRecord with no product added yet raises StrayRecord."""
    builder = NelfoVareFilBuilder()

    with pytest.raises(StrayRecord):
        builder.add_record(alternative(), line_number=1, line_content=VA_SAMPLE)


def test_stray_additional_info_before_any_product_raises():
    """An AdditionalInfoLineRecord with no product added yet raises StrayRecord."""
    builder = NelfoVareFilBuilder()

    with pytest.raises(StrayRecord):
        builder.add_record(additional_info(), line_number=1, line_content=VX_SAMPLE)


def test_mark_product_invalid_makes_next_child_stray():
    """After mark_product_invalid(), a following VX/VA is treated as stray
    even though a product was previously added - mirrors the parser's
    policy of discarding orphaned children of a line that failed to parse."""
    builder = NelfoVareFilBuilder()
    builder.add_record(product(), line_number=1, line_content=VL_SAMPLE)

    builder.mark_product_invalid()

    with pytest.raises(StrayRecord):
        builder.add_record(additional_info(), line_number=2, line_content=VX_SAMPLE)


def test_products_preserve_insertion_order():
    """build() returns products in the order they were added, not sorted
    by vare_nr or any other key."""
    builder = NelfoVareFilBuilder()
    builder.add_record(header(), line_number=1, line_content=VH_SAMPLE)
    builder.add_record(product(VL_SAMPLE), line_number=2, line_content=VL_SAMPLE)
    builder.add_record(product(VL_SAMPLE_2), line_number=3, line_content=VL_SAMPLE_2)

    nelfo_file = builder.build()

    assert [p.vare_nr for p in nelfo_file.products] == ["1016420", "1067030"]
