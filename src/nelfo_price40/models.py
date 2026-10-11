from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal, Self, TypeVar

from pydantic import BaseModel, Field, field_validator

from .enums import LinjeStatus, MaaleEnhet, PostType, Pristype, VareMrk, VaType
from .exceptions import DuplicateRecord, StrayRecord

# TODO: requires-python = ">=3.14" in pyproject.toml is probably load-bearing,
# not an arbitrary choice - the unquoted forward references below
# (list[AlternativeLineRecord] used before that class is defined) only
# work because Python 3.14 lazily evaluates annotations by default
# (PEP 649/749). Document this explicitly so nobody lowers the Python
# requirement later without realizing why it breaks.


class NelfoVareFilBuilder:
    def __init__(self):
        self._header: HeaderLineRecord | None = None
        self._unique_products: dict[str, ProductLineRecord] = {}
        self._products: list[ProductLineRecord] = []
        self._last_product: ProductLineRecord | None = None

    def add_record(self, record: Record, line_number: int, line_content: str) -> None:
        match record:
            case HeaderLineRecord():
                self._set_header(record, line_number, line_content)
            case ProductLineRecord():
                self._add_product(record, line_number, line_content)
            case AlternativeLineRecord():
                self._add_alternative_line(record, line_number, line_content)
            case AdditionalInfoLineRecord():
                self._add_additional_info_line(record, line_number, line_content)
            case _:
                raise ValueError(f"Unknown record type: {type(record)}")

    def _set_header(
        self, header: HeaderLineRecord, line_number: int, line_content: str
    ) -> None:
        if self._header is not None:
            raise DuplicateRecord(
                model=HeaderLineRecord,
                line_number=line_number,
                line_content=line_content,
            )
        self._header = header

    def _add_product(
        self, product: ProductLineRecord, line_number: int, line_content: str
    ) -> None:
        if product.vare_nr in self._unique_products:
            raise DuplicateRecord(
                model=ProductLineRecord,
                line_number=line_number,
                line_content=line_content,
            )
        self._unique_products[product.vare_nr] = product
        self._products.append(product)
        self._last_product = product

    def _add_alternative_line(
        self,
        alternative_line: AlternativeLineRecord,
        line_number: int,
        line_content: str,
    ) -> None:
        if self._last_product is None:
            raise StrayRecord(
                model=AlternativeLineRecord,
                line_number=line_number,
                line_content=line_content,
            )
        self._last_product.add_alternative_line(alternative_line)

    def _add_additional_info_line(
        self,
        additional_info_line: AdditionalInfoLineRecord,
        line_number: int,
        line_content: str,
    ) -> None:
        if self._last_product is None:
            raise StrayRecord(
                model=AdditionalInfoLineRecord,
                line_number=line_number,
                line_content=line_content,
            )
        self._last_product.add_additional_info_line(additional_info_line)

    def mark_product_invalid(self) -> None:
        self._last_product = None

    def build(self) -> NelfoVareFil40:
        if self._header is None:
            raise ValueError("Header line is missing")
        return NelfoVareFil40(header=self._header, products=self._products)


T = TypeVar("T", bound="Record")


def RegisterRecordLine(post_type: PostType):
    def decorator(record_class: type[T]) -> type[T]:
        RecordLineRegistry.register(post_type, record_class)
        return record_class

    return decorator


class RecordLineRegistry:
    registry: dict[PostType, type[Record]] = {}

    @classmethod
    def register(cls, post_type: PostType, record_class: type[Record]) -> None:
        cls.registry[post_type] = record_class

    @classmethod
    def get_record(cls, post_type: PostType) -> type[Record]:
        if post_type not in cls.registry:
            raise KeyError(f"No record class registered for post type: {post_type}")
        return cls.registry[post_type]


class Record(BaseModel):
    # TODO (docs): from_line/to_line both rely on field declaration order
    # matching the wire format's field order exactly - this is load-bearing,
    # not cosmetic. nelfo_invoice's equivalent base class documents this
    # explicitly in its docstring; worth copying that convention here so a
    # future reorder-for-readability doesn't silently break the format.
    @classmethod
    def from_line(cls, line: list[str]) -> Self:

        fields = list(cls.model_fields.keys())
        values = [value or None for value in line]
        return cls.model_validate(dict(zip(fields, values)))

    def to_line(self) -> str:
        parts = []
        for _, value in self.model_dump().items():
            if value is None:
                parts.append("")
            elif isinstance(value, date):
                parts.append(value.strftime("%Y%m%d"))
            elif isinstance(value, Enum):
                parts.append(str(value.value))
            else:
                parts.append(str(value))
        return ";".join(parts)


@RegisterRecordLine(PostType.LINJE_VAREPOST)
@RegisterRecordLine(PostType.LINJE_PRISTILBUD)
class ProductLineRecord(Record):
    post_type: Literal[PostType.LINJE_VAREPOST, PostType.LINJE_PRISTILBUD]
    vare_mrk: VareMrk
    vare_nr: str
    va_betg: str
    va_betg2: str | None = None
    maale_enhet: MaaleEnhet
    pris_enhet: str
    pris_enhet_txt: str | None = None
    pris: Decimal  # menneskelesbar desimalform, se konvertering
    mengde: Decimal
    pris_dato: date
    status: LinjeStatus = LinjeStatus.UENDRET
    blokk_nummer: str | None = None
    rabatt_gruppe: str | None = None
    fabrikat: str | None = None
    type_: str | None = None
    lagerfort: str | None = None
    salgs_pakning: Decimal | None = None
    rabatt: Decimal | None = None  # kun PL
    pristype: Pristype | None = None  # kun PL

    alternatives: list[AlternativeLineRecord] = Field(
        default_factory=list, description="List of alternative lines", exclude=True
    )
    additional_info: list[AdditionalInfoLineRecord] = Field(
        default_factory=list, description="List of additional info lines", exclude=True
    )

    @field_validator("pris_dato", mode="before")
    @classmethod
    def parse_pris_dato(cls, value: str) -> date:
        return date.fromisoformat(value)

    def add_alternative_line(self, alternative_line: AlternativeLineRecord) -> None:
        self.alternatives.append(alternative_line)

    def add_additional_info_line(
        self, additional_info_line: AdditionalInfoLineRecord
    ) -> None:
        self.additional_info.append(additional_info_line)


@RegisterRecordLine(PostType.LINJE_VARE_TILLEGSINFO)
@RegisterRecordLine(PostType.LINJE_PRISTILBUD_TILLEGSINFO)
class AdditionalInfoLineRecord(Record):
    post_type: Literal[
        PostType.LINJE_VARE_TILLEGSINFO, PostType.LINJE_PRISTILBUD_TILLEGSINFO
    ]
    feltid: str
    verdi: str


@RegisterRecordLine(PostType.LINJE_VARE_ALTERNATIV)
@RegisterRecordLine(PostType.LINJE_PRISTILBUD_ALTERNATIV)
class AlternativeLineRecord(Record):
    post_type: Literal[
        PostType.LINJE_VARE_ALTERNATIV, PostType.LINJE_PRISTILBUD_ALTERNATIV
    ]
    vare_mrk: VareMrk
    vare_nr: str
    va_type: VaType
    salgs_pakning: str | None = None


@RegisterRecordLine(PostType.HODE_VAREPOST)
@RegisterRecordLine(PostType.HODE_PRISTILBUD)
class HeaderLineRecord(Record):
    post_type: Literal[PostType.HODE_VAREPOST, PostType.HODE_PRISTILBUD]
    format: str = "EFONELFO"
    version: str = "4.0"
    selgers_id: str
    kjopers_id: str | None = None
    kunde_nr: str | None = None
    fra_dato: date
    til_dato: date | None = None
    valuta: str
    avtale_id: str | None = None
    s_firma_navn: str
    s_adr1: str | None = None
    s_adr2: str | None = None
    s_post_nr: str
    s_post_sted: str
    s_land_k: str | None = None

    @field_validator("fra_dato", "til_dato", mode="before")
    @classmethod
    def parse_date(cls, value: str | None) -> date | None:
        if value is not None:
            return date.fromisoformat(value)


class NelfoVareFil40(BaseModel):
    header: HeaderLineRecord = Field(
        ..., description="Header information for the Nelfo Vare Fil 40"
    )
    products: list[ProductLineRecord] = Field(
        default_factory=list, description="List of product lines"
    )

    def to_nelfo_text(self, line_end: str = "\r\n") -> str:
        """Serialize back to raw NELFO text.

        Defaults to "\\r\\n" since that's what real NELFO files use, and
        always ends the output with a trailing line_end (real files have
        one after the final line).

        Known limitation: ProductLineRecord stores alternatives and
        additional_info as two separate lists, so the original relative
        order between VX and VA records for a given product (which can
        vary in real files) is not preserved - alternatives are always
        written before additional_info, regardless of the order they
        were parsed in.
        """
        lines = [self.header.to_line()]
        for product in self.products:
            lines.append(product.to_line())
            for alternative in product.alternatives:
                lines.append(alternative.to_line())
            for additional_info in product.additional_info:
                lines.append(additional_info.to_line())
        return line_end.join(lines) + line_end

    def to_file(self, path: str, encoding: str = "cp1252") -> None:
        """Write to disk as raw NELFO text.

        Defaults to cp1252, matching DecoderChain's read-side fallback
        encoding - real NELFO files are commonly produced by older
        Windows-based accounting software using that codepage.
        newline="" disables Python's own newline translation so the
        "\\r\\n" built by to_nelfo_text() is written byte-for-byte,
        regardless of host OS.
        """
        with open(path, "w", encoding=encoding, newline="") as f:
            f.write(self.to_nelfo_text())
