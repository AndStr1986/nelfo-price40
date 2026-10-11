import logging

from pydantic import ValidationError

from .decoders import DecoderChain
from .enums import PostType
from .exceptions import (
    DuplicateRecord,
    RecordLineParsningError,
    StrayRecord,
    UnknownPostTypeError,
)
from .models import (
    NelfoVareFil40,
    NelfoVareFilBuilder,
    RecordLineRegistry,
)

logger = logging.getLogger(__name__)


class NelfoVareFilParser:
    def __init__(
        self,
        decoding_chain: DecoderChain | None = None,
        delimiter: str = ";",
        builder: NelfoVareFilBuilder | None = None,
    ):
        self.decoders = decoding_chain if decoding_chain is not None else DecoderChain()
        self.delimiter = delimiter
        self.builder = builder if builder is not None else NelfoVareFilBuilder()

    def parse(self, data: bytes) -> NelfoVareFil40:

        decoded_data = self.decoders.decode(data)

        for line_number, line in enumerate(decoded_data.splitlines(), start=1):
            try:
                fields = line.split(self.delimiter)
                try:
                    post_type = PostType(fields[0])
                except ValueError:
                    raise UnknownPostTypeError(
                        post_type=fields[0],
                        line_number=line_number,
                        line_content=line,
                    )
                record = RecordLineRegistry.get_record(post_type).from_line(fields)
                self.builder.add_record(
                    record, line_number=line_number, line_content=line
                )

            except ValidationError as e:
                err = RecordLineParsningError(original=e, line_number=line_number)
                logger.warning(f"{err}")
                self.builder.mark_product_invalid()
                continue  # skip the line and continue parsning
            except (
                RecordLineParsningError,
                UnknownPostTypeError,
                StrayRecord,
            ) as e:
                logger.warning(f"{e}")
                self.builder.mark_product_invalid()
                continue  # skip the line and continue parsning
            except DuplicateRecord as e:
                logger.critical(f"{e}")
                raise  # re-raise to stop parsning

        return self.builder.build()
