from pydantic import BaseModel, ValidationError


class LineParserError(Exception):
    """Exception raised for errors in the line parsing process."""


class UnknownPostTypeError(LineParserError):
    """Exception raised for unknown line types during parsing."""

    def __init__(self, post_type: str, line_number: int, line_content: str):
        self.post_type = post_type
        super().__init__(
            f"Unknown PostType: {post_type!r}, Line: {line_number}: {line_content!r}"
        )


class RecordLineParsningError(ValueError):
    """Exception raised for errors in parsing a record line."""

    def __init__(self, original: ValidationError, line_number: int):
        first = original.errors()[0]
        self.name = original.title
        self.field = ".".join(str(p) for p in first["loc"])
        self.reason = first["msg"]
        self.bad_value = first["input"]
        super().__init__(
            f"Error: Line: {line_number} {self.name} -- Field error '{self.field}' - {self.reason} (bad value: {self.bad_value!r})"
        )


class DuplicateRecord(Exception):
    """Exception raised for errors in the record processing."""

    def __init__(self, model: type[BaseModel], line_number: int, line_content: str):
        self.model = model
        super().__init__(
            f"Error: Duplicate record found: {model.__name__} at line {line_number}: {line_content!r}"
        )


class StrayRecord(Exception):
    """Exception raised for errors in the record processing."""

    def __init__(self, model: type[BaseModel], line_number: int, line_content: str):
        self.model = model
        super().__init__(
            f"Error: Line: {line_number} {model.__name__} -- Record without parrent product found. {line_content!r}"
        )


class DecoderError(Exception):
    """Exception raised for errors in the decoding process."""

    def __init__(self, decoder_name: str, original: UnicodeDecodeError):
        self.name = decoder_name
        self.original = original
        self.encoding = getattr(original, "encoding", None)
        self.reason = getattr(original, "reason", None)
        self.start = getattr(original, "start", None)
        self.data = getattr(original, "object", None)
        self.line_number = (
            self.data[: self.start].count(b"\n") + 1 if self.data else None
        )
        self.line_start = (
            self.data.rfind(b"\n", 0, self.start) + 1 if self.data else None
        )
        self.position_in_line = (
            self.start - self.line_start if self.data and self.start else None
        )
        super().__init__(
            f"Error: {self.reason!r} | Line: {self.line_number} | position: {self.position_in_line} -- trying next decoder if available"
        )


class AllDecodersFailedError(LineParserError):
    """Exception raised when all decoders fail to parse a line."""

    def __init__(self, exceptions: list[DecoderError]):
        self.exceptions = exceptions
        super().__init__(
            f"All {len(self.exceptions)} decoders failed to decode: {[e.name for e in self.exceptions]}."
        )
