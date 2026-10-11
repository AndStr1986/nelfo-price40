from enum import Enum


class VareMrk(int, Enum):
    UKJENT = 0
    ELNUMMER = 1
    EAN = 2
    PRODUSENTENS_VARENR = 3
    NRF_NUMMER = 4
    TILLEGGSVARE = 9


class MaaleEnhet(int, Enum):
    STYKK = 1
    METER = 2
    LITER = 3
    KILOGRAM = 4


class LinjeStatus(int, Enum):
    UENDRET = 0
    NY = 1
    ENDRET = 2
    UTGAAR = 3


class VaType(str, Enum):
    ALTERNATIV = "A"
    ERSTATNING = "E"
    ALT_IDENTIFIKASJON = "V"
    PAKNINGSSTORRELSE = "P"


class Pristype(str, Enum):
    BRUTTO = "B"
    NETTO = "N"


class PostType(str, Enum):
    HODE_VAREPOST = "VH"
    HODE_PRISTILBUD = "PH"
    LINJE_VAREPOST = "VL"
    LINJE_PRISTILBUD = "PL"
    LINJE_VARE_TILLEGSINFO = "VX"
    LINJE_PRISTILBUD_TILLEGSINFO = "PX"
    LINJE_VARE_ALTERNATIV = "VA"
    LINJE_PRISTILBUD_ALTERNATIV = "PA"
