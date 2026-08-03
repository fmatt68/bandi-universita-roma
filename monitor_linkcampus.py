import re
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString


URL_LINK_CAMPUS = "https://unilink.it/ateneo/bandi-e-concorsi/"

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

PAROLE_SEDE_ROMA = [
    "roma",
    "sede di roma",
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
    return " ".join(str(testo).split())


def converti_data(giorno, mese, anno):
    try:
        if str(mese).isdigit():
            numero_mese = int(mese)
        else:
            numero_mese = MESI_ITALIANI[str(mese).lower()]

        return date(int(anno), numero_mese, int(giorno))
    except (ValueError, KeyError):
        return None


def estrai_date_scadenza(testo):
    date_trovate = []

    pattern_testuale = re.compile(
        r"(?:scadenza|termine)[^0-9]{0,100}"
        r"(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
        r"settembre|ottobre|novembre|dicembre)\s+"
        r"(\d{4})",
        re.IGNORECASE,
    )

    pattern_numerico = re.compile(
        r"(?:scadenza|termine)[^0-9]{0,100}"
        r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})",
        re.IGNORECASE,
    )

    for giorno, mese, anno in pattern_testuale.findall(testo):
        valore = converti_data(giorno, mese, anno)
        if valore is not None and valore not in date_trovate:
            date_trovate.append(valore)

    for giorno, mese, anno in pattern_numerico.findall(testo):
        valore = converti_data(giorno, mese, anno)
        if valore is not None and valore not in date_trovate:
            date_trovate.append(valore)

    return date_trovate


def scegli_scadenza(date_trovate):
    if not date_trovate:
        return None

    date_future = [
        valore for valore in date_trovate if valore >= date.today()
    ]

    if date_future:
        # In presenza di riapertura termini, la scadenza valida e'
        # normalmente la data futura piu' recente.
        return max(date_future)

    return max(date_trovate)


def raccogli_dati_procedura(elemento, massimo=20):
    testi = []

    for precedente in elemento.previous_elements:
        if not isinstance(precedente, NavigableString):
            continue

        testo = normalizza_testo(precedente)
        if not testo or testo in testi:
            continue

        testi.append(testo)
        testo_minuscolo = testo.lower()

        if (
            "bando di procedura selettiva" in testo_minuscolo
            and (
                "prima fascia" in testo_minuscolo
                or "seconda fascia" in testo_minuscolo
            )
        ):
            break

        if len(testi) >= massimo:
            break

    return testi


def trova_titolo(testi):
    for testo in testi:
        if "bando di procedura selettiva" in testo.lower():
            return testo
    return "Titolo non individuato"


def trova_descrizione(testi):
    for testo in testi:
        testo_minuscolo = testo.lower()
        if (
            "gruppo scientifico disciplinare" in testo_minuscolo
            or "settore scientifico disciplinare" in testo_minuscolo
        ):
            return testo
    return "Descrizione non individuata"


def contiene_area_interesse(testo):
    testo_minuscolo = testo.lower()
    return any(parola in testo_minuscolo for parola in PAROLE_AREA_INTERESSE)


def sede_roma(testo):
    testo_minuscolo = testo.lower()
    return any(parola in testo_minuscolo for parola in PAROLE_SEDE_ROMA)


def sede_fuori_roma(testo):
    testo_minuscolo = testo.lower()
    indicatori_sede = [
        "sede di lavoro prevalente:",
        "sede prevalente:",
        "sede di lavoro:",
    ]

    sede_indicata = any(
        indicatore in testo_minuscolo for indicatore in indicatori_sede
    )

    return sede_indicata and not sede_roma(testo)


def estrai_codici_area(testo):
    pattern = re.compile(
        r"\b(?:\d{2}/)?(?:BIOS|MEDS|MEDF|IINF|PHYS)-\d{2}(?:/[A-Z])?\b",
        re.IGNORECASE,
    )

    codici = []
    for corrispondenza in pattern.finditer(testo):
        codice = corrispondenza.group(0).upper()
        if codice not in codici:
            codici.append(codice)

    return codici


def main():
    print("\n=== PARSER PROFESSORI I E II FASCIA LINK CAMPUS ===\n")

    sessione = requests.Session()
    sessione.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        }
    )

    risposta = sessione.get(URL_LINK_CAMPUS, timeout=60)
    risposta.raise_for_status()

    soup = BeautifulSoup(risposta.text, "html.parser")
    procedure = []
    link_gia_visti = set()

    for elemento in soup.find_all("a", href=True):
        href = elemento.get("href", "")
        href_minuscolo = href.lower()

        if ".pdf" not in href_minuscolo:
            continue

        if "bando_pa" in href_minuscolo:
            fascia = "II fascia - Professore associato"
        elif (
            "bando_po" in href_minuscolo
            or "bando_ord" in href_minuscolo
            or "prima_fascia" in href_minuscolo
            or "i_fascia" in href_minuscolo
        ):
            fascia = "I fascia - Professore ordinario"
        else:
            continue

        link = urljoin(URL_LINK_CAMPUS, href)
        if link in link_gia_visti:
            continue

        link_gia_visti.add(link)
        testi = raccogli_dati_procedura(elemento)
        titolo = trova_titolo(testi)
        descrizione = trova_descrizione(testi)
        testo_completo = normalizza_testo(
            titolo + " " + descrizione + " " + " ".join(testi)
        )

        date_trovate = estrai_date_scadenza(testo_completo)
        scadenza = scegli_scadenza(date_trovate)

        procedure.append(
            {
                "fascia": fascia,
                "titolo": titolo,
                "descrizione": descrizione,
                "link": link,
                "codici": estrai_codici_area(testo_completo),
                "area_interesse": contiene_area_interesse(testo_completo),
                "sede_roma": sede_roma(testo_completo),
                "sede_fuori_roma": sede_fuori_roma(testo_completo),
                "scadenza": scadenza,
                "aperta": scadenza is not None and scadenza >= date.today(),
            }
        )

    print("Bandi I e II fascia complessivi:", len(procedure))
    print(
        "Bandi di I fascia individuati:",
        sum(
            1
            for procedura in procedure
            if procedura["fascia"].startswith("I fascia")
        ),
    )
    print(
        "Bandi di II fascia individuati:",
        sum(
            1
            for procedura in procedure
            if procedura["fascia"].startswith("II fascia")
        ),
    )

    procedure_interessanti = [
        procedura
        for procedura in procedure
        if procedura["area_interesse"] and not procedura["sede_fuori_roma"]
    ]

    print(
        "Bandi in area scientifica e non fuori Roma:",
        len(procedure_interessanti),
    )

    procedure_aperte = [
        procedura
        for procedura in procedure_interessanti
        if procedura["aperta"]
    ]

    procedure_aperte.sort(
        key=lambda procedura: (procedura["scadenza"], procedura["titolo"])
    )

    print("Bandi pertinenti ancora aperti:", len(procedure_aperte))
    print("\n=== TUTTI I BANDI PERTINENTI ===")

    for numero, procedura in enumerate(procedure_interessanti, start=1):
        print("\n========================================")
        print("BANDO", numero)
        print("========================================")
        print("Fascia:", procedura["fascia"])
        print("Titolo:", procedura["titolo"])
        print("Descrizione:", procedura["descrizione"])
        print(
            "Codici area:",
            ", ".join(procedura["codici"])
            if procedura["codici"]
            else "Non individuati",
        )
        print(
            "Sede Roma:",
            "Si"
            if procedura["sede_roma"]
            else "Non esplicitamente indicata",
        )
        print(
            "Scadenza:",
            procedura["scadenza"].strftime("%d/%m/%Y")
            if procedura["scadenza"] is not None
            else "Non individuata",
        )
        print(
            "Stato:",
            "APERTO" if procedura["aperta"] else "SCADUTO",
        )
        print("Link:", procedura["link"])

    print("\n=== FINE VERIFICA PROFESSORI I E II FASCIA ===")


if __name__ == "__main__":
    main()
