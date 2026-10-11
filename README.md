# nelfo-price40

Parser for EFO/NELFO Vareformat 4.0 pris-/varefiler — det semikolonseparerte
filformatet norske elektrogrossister bruker for å sende produkt- og
prisinformasjon mellom systemer.

## Installasjon

```bash
uv add nelfo-price40
```

## Bruk

```python
from nelfo_price40 import NelfoVareFilParser

with open("varer.txt", "rb") as f:
    data = f.read()

parser = NelfoVareFilParser()
nelfo_file = parser.parse(data)

print(nelfo_file.header.s_firma_navn)
for product in nelfo_file.products:
    print(product.vare_nr, product.va_betg, product.pris)
    for alt in product.alternatives:
        print("  alternativ:", alt.vare_nr)
    for info in product.additional_info:
        print("  tilleggsinfo:", info.feltid, "=", info.verdi)
```

`parse()` tar imot rå bytes (ikke en allerede dekodet streng) — biblioteket
dekoder selv, med fallback fra UTF-8 til cp1252, siden ekte filer fra eldre
Windows-baserte systemer ofte bruker cp1252 ("ANSI"), ikke UTF-8.

## Filformatet

En varefil består av poster separert med semikolon, én post per linje:

| Posttype | Betyr | Forekomst |
|---|---|---|
| `VH` / `PH` | Fil-hode | Nøyaktig én per fil |
| `VL` / `PL` | Produktlinje | 0 eller flere |
| `VX` / `PX` | Tilleggsinfo til forrige produktlinje | 0 eller flere per produkt |
| `VA` / `PA` | Alternativ til forrige produktlinje | 0 eller flere per produkt |

`V`-prefiks = varefil, `P`-prefiks = pristilbudsfil — begge håndteres likt
av parseren.

## Datamodeller

Alt er Pydantic-modeller (`nelfo_price40.models`), re-eksportert fra
toppnivå:

- `HeaderLineRecord` — filhodet (`VH`/`PH`)
- `ProductLineRecord` — én produktlinje, med `alternatives` og
  `additional_info` fylt ut av parseren
- `AlternativeLineRecord` — ett alternativ (`VA`/`PA`)
- `AdditionalInfoLineRecord` — én tilleggsinfo-post (`VX`/`PX`), fri
  nøkkel/verdi (`feltid`/`verdi`) siden spec-en definerer dette som et
  åpent, utvidbart sett
- `NelfoVareFil40` — hele fila: `header` + `products`

Alle record-typer arver `from_line()`/`to_line()` for å bygge fra, og
serialisere tilbake til, én rå tekstlinje.

## Feilhåndtering

Parseren er **feiltolerant på linjenivå**: en ugyldig linje logges og
hoppes over, resten av fila parses videre. To unntak er fatale og avbryter
hele parsingen:

- To `VH`-poster i samme fil
- To produktlinjer med samme `vare_nr`

| Exception | Når | Fatal? |
|---|---|---|
| `UnknownPostTypeError` | Ukjent posttype (ikke VH/VL/VX/VA e.l.) | Nei — hoppes over |
| `RecordLineParsningError` | Et felt på linja er ugyldig (feil enum-verdi, feil format) | Nei — hoppes over |
| `StrayRecord` | En `VX`/`VA` dukker opp uten en gyldig forutgående `VL` | Nei — hoppes over |
| `DuplicateRecord` | Duplikat `VH` eller duplikat `vare_nr` | **Ja** |
| `AllDecodersFailedError` | Ingen av dekoderne klarte å lese bytes i det hele tatt | **Ja** |

Alle unntak arver fra `Exception` direkte (unntatt `RecordLineParsningError`,
som arver `ValueError`) og bærer strukturerte attributter (f.eks.
`e.field`, `e.reason`, `e.bad_value` på `RecordLineParsningError`) — ikke
bare en tekststreng.

### Logging

Biblioteket logger via standard `logging`-modulen (`nelfo_price40.decoders`,
`nelfo_price40.parsers`), men konfigurerer aldri selv noen handler. For å se
loggene i din egen applikasjon:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Utvidelse

Nye posttyper kan registreres uten å endre parseren, via
`RegisterRecordLine`:

```python
from nelfo_price40.models import Record, RegisterRecordLine
from nelfo_price40.enums import PostType

@RegisterRecordLine(PostType.LINJE_VAREPOST)
class MinEgneRecord(Record):
    ...
```

## Utvikling

```bash
uv sync
uv run pytest
```
