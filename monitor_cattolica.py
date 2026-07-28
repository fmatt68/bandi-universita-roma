import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit


BASE_URL = (
    "https://progetti.unicatt.it"
)

URL_INDICE_ROMA = (
    "https://progetti.unicatt.it/"
    "progetti-ateneo-concorsi-roma"
)


PAGINE_PRIMA_FASCIA = [
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 18"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-di-professori-"
            "di-prima-e-seconda-fascia-legge-240-2010-art-18"
        )
    },
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 7, commi 5-bis e 5-ter"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-di-professori-"
            "di-prima-e-seconda-fascia-legge-240-2010-art-7"
        )
    },
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 24, comma 6"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-diretta-di-"
            "professore-di-i-e-ii-fascia-legge-240-2010-"
            "art-24-comma-6"
        )
    }
]


PAROLE_PAGINA_DOCENZA = [
    "conferimento insegnamenti",
    "conferimento di insegnamenti",
    "incarichi di insegnamento",
    "incarico di insegnamento",
    "bandi conferimento incarichi",
    "copertura discipline",
    "docenti a contratto",
    "docente a contratto",
    "professori a contratto",
    "professore a contratto"
]


PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore universitario di prima fascia",
    "professore di ruolo di prima fascia",
    "posti di professore di ruolo di prima fascia",
    "posto di professore di ruolo di prima fascia"
]


PAROLE_DOCENZA_CONTRATTO = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "professore a contratto",
    "professori a contratto",
    "insegnamento a contratto",
    "insegnamenti a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento di insegnamento",
    "conferimento di insegnamenti",
    "conferimento insegnamento",
    "conferimento insegnamenti",
    "bando conferimento incarichi",
    "bandi conferimento incarichi",
    "contratto di insegnamento",
    "contratti di insegnamento",
    "attivita didattica",
    "attività didattica",
    "didattica integrativa",
    "incarico di docenza",
    "incarichi di docenza",
    "scuola di specializzazione",
    "scuole di specializzazione"
]


PAROLE_DA_ESCLUDERE = [
    "seconda fascia",
    "ii fascia",
    "revoca",
    "commissione",
    "nomina commissione",
    "approvazione atti",
    "approvazione degli atti",
    "verbale",
    "graduatoria",
    "esito",
    "regolamento",
    "modulo",
    "allegato",
    "rinuncia",
    "convocazione"
]


PATTERN_SETTORI_INTERESSE = [
    r"\b\d{2}/MEDS-\d{2}\b",
    r"\bMEDS-\d{2}/[A-Z]\b",

    r"\b\d{2}/MEDF-\d{2}\b",
    r"\bMEDF-\d{2}/[A-Z]\b",

    r"\b\d{2}/BIOS-\d{2}\b",
    r"\bBIOS-\d{2}/[A-Z]\b",

    r"\b\d{2}/MVET-\d{2}\b",
    r"\bMVET-\d{2}/[A-Z]\b",

    r"\b\d{2}/IINF-\d{2}\b",
    r"\bIINF-\d{2}/[A-Z]\b",

    r"\b\d{2}/PHYS-\d{2}\b",
    r"\bPHYS-\d{2}/[A-Z]\b",

    r"\bBIO/\d{2}\b",
    r"\bMED/\d{2}\b",
    r"\bVET/\d{2}\b",
    r"\bFIS/\d{2}\b",
    r"\bING-INF/\d{2}\b"
]


MESI_ITALIANI = (
    "gennaio|febbraio|marzo|aprile|maggio|"
    "giugno|luglio|agosto|settembre|ottobre|"
    "novembre|dicembre"
)


def crea_sessione():

    sessione = requests.Session()

    sessione.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": (
                "it-IT,it;q=0.9,en;q=0.8"
            )
        }
    )

    return sessione


def scarica_pagina(
    sessione,
    url
):

    risposta = sessione.get(
        url,
        timeout=60
    )

    print(
        "Status code:",
        risposta.status_code
    )

    print(
        "URL finale:",
        risposta.url
    )

    print(
        "Dimensione HTML:",
        len(risposta.text)
    )

    risposta.raise_for_status()

    return risposta.text


def normalizza_testo(testo):

    return " ".join(
        testo.split()
    )


def normalizza_link(href):

    link = urljoin(
        BASE_URL,
        href
    )

    parti = urlsplit(
        link
    )

    return urlunsplit(
        (
            parti.scheme,
            parti.netloc,
            parti.path,
            parti.query,
            ""
        )
    )


def e_link_documento(link):

    link_lower = link.lower()

    estensioni = [
        ".pdf",
        ".doc",
        ".docx"
    ]

    return any(
        estensione in link_lower
        for estensione in estensioni
    )


def contiene_parola_esclusa(testo):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in PAROLE_DA_ESCLUDERE
    )


def e_prima_fascia(testo):

    testo_lower = testo.lower()

    if contiene_parola_esclusa(
        testo
    ):

        return False

    return any(
        parola in testo_lower
        for parola in PAROLE_PRIMA_FASCIA
    )


def e_docenza_contratto(testo):

    testo_lower = testo.lower()

    if contiene_parola_esclusa(
        testo
    ):

        return False

    return any(
        parola in testo_lower
        for parola in PAROLE_DOCENZA_CONTRATTO
    )


def contiene_settore_interesse(testo):

    testo_maiuscolo = testo.upper()

    return any(
        re.search(
            pattern,
            testo_maiuscolo
        )
        for pattern in PATTERN_SETTORI_INTERESSE
    )


def estrai_codici_area(testo):

    testo_maiuscolo = testo.upper()

    codici = []

    for pattern in PATTERN_SETTORI_INTERESSE:

        risultati = re.findall(
            pattern,
            testo_maiuscolo
        )

        for codice in risultati:

            if codice not in codici:

                codici.append(
                    codice
                )

    return codici


def estrai_scadenze(testo):

    risultati = []

    pattern_numerico = re.compile(
        r"scadenza\s*:?\s*"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    pattern_testuale = re.compile(
        r"scadenza\s*:?\s*"
        r"(\d{1,2}\s+(?:"
        + MESI_ITALIANI
        + r")\s+\d{4})",
        re.IGNORECASE
    )

    risultati.extend(
        pattern_numerico.findall(
            testo
        )
    )

    risultati.extend(
        pattern_testuale.findall(
            testo
        )
    )

    risultati_unici = []

    for risultato in risultati:

        risultato = normalizza_testo(
            risultato
        )

        if risultato not in risultati_unici:

            risultati_unici.append(
                risultato
            )

    return risultati_unici


def trova_contenitore_documento(
    elemento
):

    nodo = elemento

    miglior_nodo = elemento.parent

    for _ in range(8):

        if nodo is None:

            break

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        testo_lower = testo.lower()

        if len(testo) < 3500:

            miglior_nodo = nodo

        if (
            "scadenza" in testo_lower
            and len(testo) < 3500
        ):

            return nodo

        nodo = nodo.parent

    return miglior_nodo


def scopri_pagine_docenza(
    sessione
):

    print(
        "\nRicerca automatica pagine docenza "
        "nella pagina indice Roma"
    )

    html = scarica_pagina(
        sessione,
        URL_INDICE_ROMA
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    pagine = {}

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        href = elemento.get(
            "href"
        )

        if not titolo or not href:

            continue

        titolo_lower = titolo.lower()

        if not any(
            parola in titolo_lower
            for parola in PAROLE_PAGINA_DOCENZA
        ):

            continue

        link = normalizza_link(
            href
        )

        if "progetti-ateneo-roma-" not in link.lower():

            continue

        pagine[
            link
        ] = {
            "nome": titolo,
            "tipo": "docenza",
            "url": link
        }

    print(
        "Pagine docenza Roma individuate:",
        len(pagine)
    )

    for pagina in pagine.values():

        print(
            "PAGINA DOCENZA:",
            pagina["nome"]
        )

        print(
            "URL:",
            pagina["url"]
        )

    return list(
        pagine.values()
    )


def analizza_pagina(
    nome,
    tipo,
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    print(
        "\n========================================"
    )

    print(
        "SEZIONE:",
        nome
    )

    print(
        "TIPO:",
        tipo
    )

    print(
        "========================================"
    )

    risultati = []

    links_visti = set()

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        href = elemento.get(
            "href"
        )

        if not href:

            continue

        link = normalizza_link(
            href
        )

        if link in links_visti:

            continue

        if not e_link_documento(
            link
        ):

            continue

        titolo_link = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        contenitore = trova_contenitore_documento(
            elemento
        )

        testo_blocco = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True
            )
        )

        testo_completo = normalizza_testo(
            titolo_link
            + " "
            + testo_blocco
            + " "
            + link
        )

        if tipo == "prima_fascia":

            ammesso = e_prima_fascia(
                testo_completo
            )

        elif tipo == "docenza":

            ammesso = e_docenza_contratto(
                testo_completo
            )

        else:

            ammesso = False

        if not ammesso:

            continue

        links_visti.add(
            link
        )

        scadenze = estrai_scadenze(
            testo_blocco
        )

        codici_area = estrai_codici_area(
            testo_completo
        )

        risultato = {
            "titolo": titolo_link,
            "testo": testo_blocco,
            "link": link,
            "scadenze": scadenze,
            "codici_area": codici_area,
            "area_interesse": contiene_settore_interesse(
                testo_completo
            )
        }

        risultati.append(
            risultato
        )

    print(
        "PROCEDURE PERTINENTI TROVATE:",
        len(risultati)
    )

    for numero, risultato in enumerate(
        risultati,
        start=1
    ):

        print(
            "\n----------------------------------------"
        )

        print(
            "PROCEDURA:",
            numero
        )

        print(
            "TITOLO LINK:",
            risultato["titolo"]
        )

        print(
            "AREA DI INTERESSE:",
            risultato["area_interesse"]
        )

        print(
            "CODICI AREA:",
            risultato["codici_area"]
        )

        print(
            "SCADENZE:",
            risultato["scadenze"]
        )

        print(
            "LINK:",
            risultato["link"]
        )

        print(
            "TESTO BLOCCO:",
            risultato["testo"][:1800]
        )

    return risultati


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== DIAGNOSTICA CATTOLICA ROMA ===\n"
)

sessione = crea_sessione()

pagine_docenza = scopri_pagine_docenza(
    sessione
)

pagine_da_controllare = (
    PAGINE_PRIMA_FASCIA
    + pagine_docenza
)

totale_procedure = 0

for pagina in pagine_da_controllare:

    print(
        "\n\nControllo:",
        pagina["nome"]
    )

    try:

        html = scarica_pagina(
            sessione,
            pagina["url"]
        )

        risultati = analizza_pagina(
            pagina["nome"],
            pagina["tipo"],
            html
        )

        totale_procedure += len(
            risultati
        )

    except Exception as errore:

        print(
            "ERRORE:",
            pagina["nome"]
        )

        print(
            str(
                errore
            )
        )

print(
    "\nTOTALE PROCEDURE PERTINENTI:",
    totale_procedure
)

print(
    "\n=== FINE DIAGNOSTICA CATTOLICA ROMA ==="
)
