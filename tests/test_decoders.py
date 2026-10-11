"""Tests for DecoderChain (tries each decoder in turn until one succeeds).

Covers:
- Plain UTF-8 data decodes via the first decoder in the chain
- Data that's invalid UTF-8 but valid cp1252 falls through to cp1252
- Data invalid for every decoder in the chain raises DecoderError
  (regression test for a real bug: the fallback used to be a bare
  `raise` with no active exception, crashing with an unrelated
  RuntimeError instead of surfacing the actual decode failure)
"""

import pytest

from nelfo_price40 import AllDecodersFailedError, DecoderError
from nelfo_price40.decoders import Decoder, DecoderChain


def test_decodes_plain_utf8():
    """Ordinary UTF-8 bytes decode successfully via the first decoder."""
    text = DecoderChain().decode("Hello, æøå".encode("utf-8"))
    assert text == "Hello, æøå"


def test_falls_back_to_cp1252_for_invalid_utf8():
    """A byte sequence that's invalid UTF-8 but valid cp1252 (e.g. a
    single-byte 'Ø' = 0xD8) falls through to the cp1252 decoder instead
    of failing outright."""
    data = "R".encode("utf-8") + b"\xd8" + "D".encode("utf-8")
    text = DecoderChain().decode(data)
    assert text == "RØD"


def test_raises_decoder_error_when_every_decoder_fails():
    """A byte invalid under every decoder in the chain (0x81 is undefined
    in both utf-8 and cp1252) raises a DecoderError describing the last
    attempted decoder's failure, not an unrelated RuntimeError."""
    with pytest.raises(AllDecodersFailedError):
        DecoderChain().decode(b"\x81")


def test_decoder_chain_adapter():

    class latin1Decoder(Decoder):
        def decode(self, data: bytes) -> str:

            try:
                return data.decode("latin-1")
            except UnicodeDecodeError as e:
                raise DecoderError(decoder_name=type(self).__name__, original=e) from e

    chain = DecoderChain()
    assert chain.list_decoders() == ["utf8Decoder", "cp1252Decoder"]

    chain.add_decoder(latin1Decoder())
    assert chain.list_decoders() == ["utf8Decoder", "cp1252Decoder", "latin1Decoder"]
