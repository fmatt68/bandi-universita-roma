import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = (
    "https://www.unicampus.it"
)


PAGINE_UNICAMPUS = [
    {
        "nome": (
            "Professori I e II fascia "
            "- Procedure selettive"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "professori-i-e-ii-procedure-selettive/"
        )
    },
    {
        "nome": (
            "Professori I e II fascia "
            "- Procedure valutative"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "professori-i-e-ii-procedure-valutative/"
        )
    },
    {
        "nome": (
            "Docenti a contratto"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "docenti-a-contratto/"
        )
    },
    {
        "nome": (
            "Manifestazioni di interesse"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "manifestazioni-di-interesse/"
        )
    },
    {
        "nome": (
            "Manifestazioni di interesse "
            "- Foundation Year"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "manifestazioni-di-interesse-foundation-year/"
        )
    }
]


PAROLE_LINK_UTILI = [
    "prima fascia",
    "i fascia",
    "selettiva i fascia",
    "valutativa i fascia",
    "docente a contratto",
    "docenti a contratto",
    "insegnamento",
    "didattica",
    "manifestazione di interesse",
    "manifestazioni di interesse",
    "incarico",
    "bando",
    "avviso",
    "ord/"
]


def scarica_pagina(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; MonitorBandi/1.0)"
        )
    }

    risposta = requests.get(
        url,
        headers=headers,
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

    link = link.split(
        "#"
    )[0]

    return link


def estrai_sezione_in_atto(testo):

    testo_lower = testo.lower()

    posizione_inizio = testo_lower.find(
        "in atto"
    )

    if posizione_inizio == -1:

        return ""

    posizione_fine = testo_lower.find(
        "conclusi",
        posizione_inizio
    )

    if posizione_fine == -1:

        posizione_fine = len(
            testo
        )

    return testo[
        posizione_inizio:posizione_fine
    ]


def link_potenzialmente_utile(
    titolo,
    href
):

    titolo_lower = titolo.lower()

    href_lower = href.lower()

    if "/ateneo/concorsi/" not in href_lower:

        return False

    pagine_generali = [
        "/ateneo/concorsi/",
        "/ateneo/concorsi/professori-i-e-ii-"
        "procedure-selettive/",
        "/ateneo/concorsi/professori-i-e-ii-"
        "procedure-valutative/",
        "/ateneo/concorsi/docenti-a-contratto/",
        "/ateneo/concorsi/manifestazioni-di-interesse/",
        "/ateneo/concorsi/manifestazioni-di-interesse-"
        "foundation-year/"
    ]

    percorso = href_lower.split(
        "?"
    )[0]

    if percorso in pagine_generali:

        return False

    return any(
        parola in titolo_lower
        or parola in href_lower
        for parola in PAROLE_LINK_UTILI
    )


def analizza_pagina(
    nome,
    url,
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    testo = soup.get_text(
        "\n",
        strip=True
    )

    sezione_in_atto = estrai_sezione_in_atto(
        testo
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

    if sezione_in_atto:

        print(
            "CONTENUTO DELLA SEZIONE IN ATTO:\n"
        )

        print(
            sezione_in_atto[:6000]
        )

    else:

        print(
            "SEZIONE IN ATTO NON INDIVIDUATA"
        )

        print(
            "\nPRIMI 3000 CARATTERI DELLA PAGINA:\n"
        )

        print(
            testo[:3000]
        )

    print(
        "\nLINK POTENZIALMENTE UTILI:\n"
    )

    links_trovati = []

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        href = elemento.get(
            "href"
        )

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not href:

            continue

        link_completo = normalizza_link(
            href
        )

        if not titolo:

            continue

        if not link_potenzialmente_utile(
            titolo,
            link_completo
        ):

            continue

        if link_completo in links_trovati:

            continue

        links_trovati.append(
            link_completo
        )

        print(
            "TITOLO:",
            titolo
        )

        print(
            "LINK:",
            link_completo
        )

        print()

    print(
        "TOTALE LINK POTENZIALMENTE UTILI:",
        len(
            links_trovati
        )
    )


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== TEST MONITOR CAMPUS BIO-MEDICO ===\n"
)

for pagina in PAGINE_UNICAMPUS:

    print(
        "\n\nAPERTURA SEZIONE:",
        pagina["nome"]
    )

    try:

        html = scarica_pagina(
            pagina["url"]
        )

        analizza_pagina(
            pagina["nome"],
            pagina["url"],
            html
        )

    except Exception as errore:

        print(
            "ERRORE NELLA SEZIONE:",
            pagina["nome"]
        )

        print(
            str(
                errore
            )
        )

print(
    "\n=== FINE TEST CAMPUS BIO-MEDICO ===\n"
)
