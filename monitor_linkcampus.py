import re
import requests

from datetime import date
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

PAROLE_AREA_INTERESSE = [
    "bios-",
    "biologia",
    "biochimica",
    "biotecnologie",
    "genetica",
    "istologia",
    "immunologia",
    "microbiologia",
    "patologia",
    "oncologia",
    "ematologia",
    "meds-",
    "medf-",
    "medicina",
    "chirurgia",
    "farmacologia",
    "fisiologia",
    "neuroscienze",
    "iinf-",
    "informatica",
    "bioinformatica",
    "phys-",
    "fisica",
]

PAROLE[
bios-",
biologia",
biochimica",
de di roma",
    "sede prevalente roma",
    "sede di lavoro roma",
    "sede di lavoro prevalente: roma",
]

MESI_ITALIANI = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


def normalizza_testo(testo):
    return " ".join(
        str(testo).split()
    )


def converti_data(
    giorno,
    mese,
    anno
):
    try:
        if str(mese).isdigit():
            numero_mese = int(mese)
        else:
            numero_mese = MESI_ITALIANI[
                str(mese).lower()
            ]

        return date(
            int(anno),
            numero_mese,
            int(giorno)
        )

    except (
        ValueError,
        KeyError
    ):
        return None


def estrai_date_scadenza(testo):
    date_trovate = []

    pattern_testuale = re.compile(
        r"(?:scadenza|termine)"
        r"[^0-9]{0,100}"
        r"(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|"
        r"giugno|luglio|agosto|settembre|ottobre|"
        r"novembre|dicembre)\s+"
        r"(\d{4})",
        re.IGNORECASE
    )

    pattern_numerico = re.compile(
        r"(?:scadenza|termine)"
        r"[^0-9]{0,100}"
        r"(\d{1,2})[/.-]"
        r"(\d{1,2})[/.-]"
        r"(\d{4})",
        re.IGNORECASE
    )

    for giorno, mese, anno in pattern_testuale.findall(
        testo
    ):
        valore = converti_data(
            giorno,
            mese,
            anno
        )

        if (
            valore is not None
            and valore not in date_trovate
        ):
            date_trovate.append(
                valore
            )

    for giorno, mese, anno in pattern_numerico.findall(
        testo
    ):
        valore = converti_data(
            giorno,
            mese,
            anno
        )

        if (
            valore is not None
            and valore not in date_trovate
        ):
            date_trovate.append(
                valore
            )

    return date_trovate


def scegli_scadenza(date_trovate):
    if not date_trovate:
        return None

    date_future = [
        valore
        for valore in date_trovate
        if valore >= date.today()
    ]

    if date_future:
        return max(
            date_future
        )

    return max(
        date_trovate
    )


def raccogli_dati_procedura(elemento):
    testi = []

    for precedente in elemento.previous_elements:
        if not isinstance(
            precedente,
            NavigableString
        ):
            continue

        testo = normalizza_testo(
            precedente
        )

        if not testo:
            continue

        if testo in testi:
            continue

        testi.append(
            testo
        )

        testo_minuscolo = testo.lower()

        if (
            "bando di procedura selettiva"
            in testo_minuscolo
            and (
                "prima fascia"
                in testo_minuscolo
                or "seconda fascia"
                in testo_minuscolo
            )
        ):
            break

        if len(testi) >= 20:
            break

    return testi


def trova_titolo(testi):
    for testo in testi:
        testo_minuscolo = testo.lower()

        if (
            "bando di procedura selettiva"
            in testo_minuscolo
        ):
            return testo

    return "Titolo non individuato"


def trova_descrizione(testi):
    for testo in testi:
        testo_minuscolo = testo.lower()

        if (
            "gruppo scientifico disciplinare"
            in testo_minuscolo
            or "settore scientifico disciplinare"
            in testo_minuscolo
        ):
            return testo

    return "Descrizione non individuata"


def contiene_area_interesse(testo):
    testo_minuscolo = testo.lower()

    return any(
        parola in testo_minuscolo
        for parola in PAROLE_AREA_INTERESSE
    )


def sede_roma(testo):
    testo_minuscolo = testo.lower()

    return any(
        parola in testo_minuscolo
        for parola in PAROLE_SEDE_ROMA
    )


def sede_fuori_roma(testo):
    testo_minuscolo = testo.lower()

    indicatori_sede = [
        "sede di lavoro prevalente:",
        "sede prevalente:",
        "sede di lavoro:"
    ]

    sede_indicata = any(
        indicatore in testo_minuscolo
        for indicatore in indicatori_sede
    )

    return (
        sede_indicata
        and not sede_roma(
            testo
        )
    )


def estrai_codici_area(testo):
    pattern = re.compile(
        r"\b(?:\d{2}/)?"
        r"(?:BIOS|MEDS|MEDF|IINF|PHYS)"
        r"-\d{2}(?:/[A-Z])?\b",
        re.IGNORECASE
    )

    codici = []

    for codice in pattern.findall(
        testo
    ):
        codice = codice.upper()

        if codice not in codici:
            codici.append(
                codice
            )

    return codici


print(
    "\n=== PARSER PROFESSORI ASSOCIATI LINK CAMPUS ===\n"
)

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

procedure = []
link_gia_visti = set()

for elemento in soup.find_all(
    "a",
    href=True
):
    href = elemento.get(
        "href",
        ""
    )

    href_minuscolo = href.lower()

    if "bando_pa" not in href_minuscolo:
        continue

    if ".pdf" not in href_minuscolo:
        continue

    link = urljoin(
        URL_LINK_CAMPUS,
        href
    )

    if link in link_gia_visti:
        continue

    link_gia_visti.add(
        link
    )

    testi = raccogli_dati_procedura(
        elemento
    )

    titolo = trova_titolo(
        testi
    )

    descrizione = trova_descrizione(
        testi
    )

    testo_completo = normalizza_testo(
        titolo
        + " "
        + descrizione
        + " "
        + " ".join(testi)
    )

    date_trovate = estrai_date_scadenza(
        testo_completo
    )

    scadenza = scegli_scadenza(
        date_trovate
    )

    procedure.append(
        {
            "titolo": titolo,
            "descrizione": descrizione,
            "link": link,
            "codici": estrai_codici_area(
                testo_completo
            ),
            "area_interesse": contiene_area_interesse(
                testo_completo
            ),
            "sede_roma": sede_roma(
                testo_completo
            ),
            "sede_fuori_roma": sede_fuori_roma(
                testo_completo
            ),
            "scadenza": scadenza,
            "aperta": (
                scadenza is not None
                and scadenza >= date.today()
            )
        }
    )

print(
    "Bandi PA complessivi:",
    len(procedure)
)

procedure_interessanti = [
    procedura
    for procedura in procedure
    if procedura["area_interesse"]
    and not procedura["sede_fuori_roma"]
]

print(
    "Bandi in area scientifica e non fuori Roma:",
    len(procedure_interessanti)
)

procedure_aperte = [
    procedura
    for procedura in procedure_interessanti
    if procedura["aperta"]
]

print(
    "Bandi pertinenti ancora aperti:",
    len(procedure_aperte)
)

print(
    "\n=== BANDI PERTINENTI APERTI ==="
)

for numero, procedura in enumerate(
    procedure_aperte,
    start=1
):
    print(
        "\n========================================"
    )
    print(
        "BANDO",
        numero
    )
    print(
        "========================================"
    )
    print(
        "Titolo:",
        procedura["titolo"]
    )
    print(
        "Descrizione:",
        procedura["descrizione"]
    )
    print(
        "Codici area:",
        ", ".join(
            procedura["codici"]
        )
        if procedura["codici"]
        else "Non individuati"
    )
    print(
        "Sede Roma:",
        "Sì"
        if procedura["sede_roma"]
        else "Non esplicitamente indicata"
    )
    print(
        "Scadenza:",
        procedura["scadenza"].strftime(
            "%d/%m/%Y"
        )
    )
    print(
        "Link:",
        procedura["link"]
    )

print(
    "\n=== FINE PARSER PROFESSORI ASSOCIATI ==="
)
