import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit


BASE_URL = (
    "https://progetti.unicatt.it"
)


PAGINE_CATTOLICA_ROMA = [
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


PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore universitario di prima fascia",
    "professore di ruolo di prima fascia"
]


PAROLE_DA_ESCLUDERE = [
    "seconda fascia",
    "ii fascia",
    "revoca",
    "commissione",
    "approvazione atti",
    "verbale",
    "graduatoria",
    "esito",
    "regolamento",
    "modulo",
    "allegato"
]


PAROLE_AREA = [
    "meds-",
    "medf-",
    "bios-",
    "mvet-",
    "iinf-",
    "phys-",
    "med/",
    "bio/",
    "vet/",
    "fis/",
    "ing-inf/",
    "medicina",
    "chirurgia",
    "odontoiatria",
    "biologia",
    "biomedicina",
    "farmacologia",
    "oncologia",
    "patologia",
    "anestesiologia",
    "neurochirurgia"
]


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


def trova_contenitore(
    elemento
):

    nodo = elemento

    for _ in range(7):

        if nodo is None:

            break

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        testo_lower = testo.lower()

        if (
            "scadenza" in testo_lower
            and len(testo) < 2500
        ):

            return nodo

        nodo = nodo.parent

    return elemento.parent


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


def e_prima_fascia(testo):

    testo_lower = testo.lower()

    if any(
        parola in testo_lower
        for parola in PAROLE_DA_ESCLUDERE
    ):

        return False

    return any(
        parola in testo_lower
        for parola in PAROLE_PRIMA_FASCIA
    )


def contiene_area_interesse(testo):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in PAROLE_AREA
    )


def estrai_scadenze(testo):

    risultati = []

    pattern_numerico = re.compile(
        r"scadenza\s+"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    pattern_testuale = re.compile(
        r"scadenza\s+"
        r"(\d{1,2}\s+"
        r"(?:gennaio|febbraio|marzo|aprile|maggio|"
        r"giugno|luglio|agosto|settembre|ottobre|"
        r"novembre|dicembre)\s+\d{4})",
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

    return risultati


def analizza_pagina(
    nome,
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
        "========================================\n"
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

        contenitore = trova_contenitore(
            elemento
        )

        testo_blocco = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True
            )
        )

        titolo_link = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        testo_completo = (
            titolo_link
            + " "
            + testo_blocco
            + " "
            + link
        )

        if not e_prima_fascia(
            testo_completo
        ):

            continue

        links_visti.add(
            link
        )

        scadenze = estrai_scadenze(
            testo_blocco
        )

        risultato = {
            "titolo": titolo_link,
            "testo": testo_blocco,
            "link": link,
            "scadenze": scadenze,
            "area": contiene_area_interesse(
                testo_completo
            )
        }

        risultati.append(
            risultato
        )

    print(
        "PROCEDURE DI PRIMA FASCIA TROVATE:",
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
            risultato["area"]
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
            risultato["testo"][:1500]
        )


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== DIAGNOSTICA CATTOLICA ROMA ===\n"
)

sessione = crea_sessione()

for pagina in PAGINE_CATTOLICA_ROMA:

    print(
        "\n\nControllo:",
        pagina["nome"]
    )

    try:

        html = scarica_pagina(
            sessione,
            pagina["url"]
        )

        analizza_pagina(
            pagina["nome"],
            html
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
    "\n=== FINE DIAGNOSTICA CATTOLICA ROMA ==="
)
