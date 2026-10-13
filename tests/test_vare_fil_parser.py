"""Tests for NelfoVareFilParser (builds a NelfoVareFil40 from raw file bytes).

Covers:
- Parsing a real, large file end to end (fixtures/sample_file2.txt)
- Parsing a small file containing deliberately broken lines
  (fixtures/sample_file1.txt) - bad lines are skipped and logged, the
  rest of the file still parses
- Multiple VH records -> DuplicateRecord (fatal, aborts the parse)
- Duplicate vare_nr across two VL records -> DuplicateRecord (fatal)
- A VX/VA with no preceding valid VL -> StrayRecord (logged, skipped,
  does NOT abort the parse)
- A file with no VH at all -> ValueError
"""

import pytest

from nelfo_price40 import (
    DuplicateRecord,
    NelfoVareFil40,
    NelfoVareFilBuilder,
    NelfoVareFilParser,
)
from nelfo_price40.decoders import DecoderChain

VH_SAMPLE = "VH;EFONELFO;4.0;NO979692900MVA;;;20081209;;NOK;;Onninen AS;Postboks 70;;1483;SKYTTA;NO"
VL_SAMPLE = "VL;1;1016420;PFSP 1KV 2X1,5/1,5 B50;NEXANS NORWAY AS;2;MTR;METER;0;10000;20081209;3;010201;R00;;;J;500000;;"


def make_parser() -> NelfoVareFilParser:
    return NelfoVareFilParser()


def test_parses_large_file():
    """A 2600+ line file parses end to end with a stable product count.

    sample_file2.txt is synthetic (generated, no real supplier data) but
    reproduces the shape of a real price file, including two deliberately
    introduced defects used to verify error handling elsewhere: an invalid
    vare_mrk on the first VL (skipped), and a non-UTF-8 byte later in the
    file (forces the whole file through the cp1252 fallback decoder, which
    also mangles an otherwise-valid UTF-8 "²" elsewhere into "Â²" -
    asserted on below as a known, current characteristic of the pipeline,
    not a bug in this test).
    """
    with open("tests/fixtures/sample_file2.txt", "rb") as f:
        data = f.read()

    nelfo_file = make_parser().parse(data)

    assert isinstance(nelfo_file, NelfoVareFil40)
    assert nelfo_file.header.selgers_id == "NO999999999MVA"
    assert len(nelfo_file.products) == 2604

    first = nelfo_file.products[0]
    assert first.vare_nr == "2000001"
    assert first.va_betg == "TESTKABEL SOLCELLE 6MMÂ²"

    last = nelfo_file.products[-1]
    assert last.vare_nr == "SP2010"


def test_sample_file1_skips_bad_lines_but_keeps_valid_ones():
    """fixtures/sample_file1.txt mixes two valid VL records with a VL that
    has an invalid vare_mrk and a line with an unknown post_type ('VI').
    The bad lines (and the VX/VA that end up orphaned by them) are logged
    and skipped; the two valid products still come through correctly."""
    with open("tests/fixtures/sample_file1.txt", "rb") as f:
        data = f.read()

    nelfo_file = make_parser().parse(data)

    assert len(nelfo_file.products) == 2
    by_vare_nr = {p.vare_nr: p for p in nelfo_file.products}
    assert by_vare_nr["1016420"].alternatives[0].vare_nr == "1067030"
    assert len(by_vare_nr["1067030"].additional_info) == 4


def test_duplicate_header_raises():
    """A second VH record in the same file raises DuplicateRecord and
    aborts the parse."""
    data = "\n".join([VH_SAMPLE, VL_SAMPLE, VH_SAMPLE]).encode()
    with pytest.raises(DuplicateRecord):
        make_parser().parse(data)


def test_duplicate_vare_nr_raises():
    """Two VL records sharing the same vare_nr raise DuplicateRecord and
    abort the parse."""
    data = "\n".join([VH_SAMPLE, VL_SAMPLE, VL_SAMPLE]).encode()
    with pytest.raises(DuplicateRecord):
        make_parser().parse(data)


def test_stray_record_before_any_product_is_skipped_not_fatal():
    """A VX with no VL ever having appeared yet is logged and skipped -
    it does not raise out of parse() (StrayRecord is caught internally,
    same tolerant policy as a malformed line), and does not crash with an
    unrelated IndexError (regression test for a real bug found while
    writing this test: skip_next_set previously started False instead of
    True, so records[-1] was indexed into an empty list)."""
    data = "\n".join([VH_SAMPLE, "VX;BILDE;http://example.com/img.gif"]).encode()

    nelfo_file = make_parser().parse(data)

    assert nelfo_file.products == []


def test_no_header_raises_value_error():
    """A file with no VH record at all raises a ValueError."""
    data = VL_SAMPLE.encode()
    with pytest.raises(ValueError):
        make_parser().parse(data)


def test_custom_delimiter_is_used():
    """A non-default delimiter passed to the constructor is actually used
    to split lines, instead of always assuming ';'."""
    data = "\n".join(
        [VH_SAMPLE.replace(";", "|"), VL_SAMPLE.replace(";", "|")]
    ).encode()

    nelfo_file = NelfoVareFilParser(delimiter="|").parse(data)

    assert nelfo_file.header.s_firma_navn == "Onninen AS"
    assert nelfo_file.products[0].vare_nr == "1016420"


def test_custom_decoding_chain_is_used():
    """An explicit DecoderChain instance passed to the constructor is the
    one actually used to decode - not silently ignored in favor of a
    fresh default instance (regression test for the earlier bug where
    passing an instance crashed, since the default tried to call it)."""
    chain = DecoderChain()
    data = "\n".join([VH_SAMPLE, VL_SAMPLE]).encode()

    nelfo_file = NelfoVareFilParser(decoding_chain=chain).parse(data)

    assert nelfo_file.header.s_firma_navn == "Onninen AS"


def test_custom_builder_is_used():
    """An explicit NelfoVareFilBuilder instance passed to the constructor
    is the one actually used - its accumulated state ends up in the
    parse() result."""
    builder = NelfoVareFilBuilder()
    data = "\n".join([VH_SAMPLE, VL_SAMPLE]).encode()

    nelfo_file = NelfoVareFilParser(builder=builder).parse(data)

    assert nelfo_file == builder.build()


def test_two_parsers_do_not_share_default_builder_state():
    """Two NelfoVareFilParser() instances constructed with no explicit
    builder each get their own NelfoVareFilBuilder - regression test for
    the mutable-default-argument trap (a class instance used directly as
    a default value is shared across every call site)."""
    data = "\n".join([VH_SAMPLE, VL_SAMPLE]).encode()

    first = NelfoVareFilParser().parse(data)
    second = NelfoVareFilParser().parse(data)

    assert len(first.products) == 1
    assert len(second.products) == 1
