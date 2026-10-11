"""Tests for NelfoVareFil40.to_nelfo_text() / to_file() (serializing a
parsed file back to raw NELFO text).

Covers:
- Lines are joined with CRLF ("\\r\\n"), matching real NELFO files
- Output ends with a trailing line_end after the last line
- to_file() writes cp1252-encoded bytes, readable back as cp1252
- A line_end override is respected
"""

from nelfo_price40 import NelfoVareFilParser


def make_file():
    with open("tests/fixtures/sample_file1.txt", "rb") as f:
        data = f.read()
    return NelfoVareFilParser().parse(data)


def test_lines_joined_with_crlf():
    """Consecutive lines in the output are separated by \\r\\n, not \\n."""
    text = make_file().to_nelfo_text()
    assert "\r\n" in text
    assert "VH;EFONELFO" in text.split("\r\n")[0]


def test_ends_with_trailing_line_end():
    """The serialized text ends with a line_end after the final line, not
    just between lines (real NELFO files have a trailing line ending)."""
    text = make_file().to_nelfo_text()
    assert text.endswith("\r\n")
    assert not text.endswith("\r\n\r\n")


def test_custom_line_end_is_respected():
    """A caller-supplied line_end overrides the "\\r\\n" default."""
    text = make_file().to_nelfo_text(line_end="\n")
    assert "\r\n" not in text
    assert text.endswith("\n")


def test_to_file_writes_cp1252(tmp_path):
    """to_file() writes bytes that decode correctly as cp1252, matching
    DecoderChain's read-side fallback encoding."""
    nelfo_file = make_file()
    path = tmp_path / "out.txt"

    nelfo_file.to_file(str(path))

    raw = path.read_bytes()
    assert raw.decode("cp1252") == nelfo_file.to_nelfo_text()
    assert b"\r\n" in raw


def test_to_file_respects_encoding_override(tmp_path):
    """An explicit encoding= argument to to_file() is honored."""
    nelfo_file = make_file()
    path = tmp_path / "out_utf8.txt"

    nelfo_file.to_file(str(path), encoding="utf-8")

    raw = path.read_bytes()
    assert raw.decode("utf-8") == nelfo_file.to_nelfo_text()
