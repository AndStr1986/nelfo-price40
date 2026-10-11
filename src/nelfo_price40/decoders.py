from abc import ABC, abstractmethod
import logging
from .exceptions import DecoderError, AllDecodersFailedError

logger = logging.getLogger(__name__)


class Decoder(ABC):
    @abstractmethod
    def decode(self, data) -> str:
        pass


class cp1252Decoder(Decoder):
    def decode(self, data: bytes) -> str:

        try:
            return data.decode("cp1252")
        except UnicodeDecodeError as e:
            raise DecoderError(decoder_name=type(self).__name__, original=e) from e


class utf8Decoder(Decoder):
    def decode(self, data: bytes) -> str:

        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise DecoderError(decoder_name=type(self).__name__, original=e) from e


class DecoderChain:
    def __init__(self):
        self.decoders = [utf8Decoder(), cp1252Decoder()]
        self.exceptions: list[DecoderError] = []

    def decode(self, data: bytes) -> str:
        for decoder in self.decoders:
            try:
                decoded_data = decoder.decode(data)
                logger.info(
                    f"Successfully decoded data using {decoder.__class__.__name__}"
                )
                return decoded_data

            except DecoderError as e:
                self.exceptions.append(e)
                logger.warning(f"{e.name}: {e}")
                continue

        raise AllDecodersFailedError(exceptions=self.exceptions)

    def add_decoder(self, decoder: Decoder):
        self.decoders.append(decoder)

    def list_decoders(self):
        return [decoder.__class__.__name__ for decoder in self.decoders]
