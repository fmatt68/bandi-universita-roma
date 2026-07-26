import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = (
    "https://web.uniroma2.it"
)

PAGINE_I_FASCIA = [
    {
        "nome": (
            "Art. 7, commi 5-bis e 5-ter "
            "- Chiamata per mobilita"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure-art-7-comma-5-bis-e-comma-5-ter-"
            "cd-chiamata-per-mobilit"
        )
    },
    {
        "nome": (
            "Art. 18, comma 1"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_art__18__comma_1"
        )
    },
    {
        "nome": (
            "Art. 18, comma 4"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_art__18__comma_4"
        )
    },
    {
        "nome": (
            "Art. 18, comma 4-ter"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure-art-18-comma-4ter"
        )
    },
    {
        "nome": (
            "Art. 24, comma 6"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_valutative_art__24__comma_6"
        )
    }
]


def scarica_pagina(url):

    risposta = requests.get(
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

    risposta.raise_for_status()

    return risposta.text


def link_potenzialmente_utile(
    titolo,
    href
):

    titolo_lower = titolo.lower()
    href_lower = href.lower()

    parole_utili = [
        "bando",
        "procedura",
        "decreto",
        "scadenza",
        "settore",
        "fascia",
        "professore",
        "pdf"
    ]

    if href_lower.endswith(
        ".pdf"
    ):

        return True

    if ".pdf?" in href_lower:

        return True

    if "/it/contenuto/" in href_lower:

        return True

    for parola in parole_utili:

        if parola in titolo_lower:

            return True

    return False


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

    print(
        "PRIMI 3000 CARATTERI DELLA PAGINA:\n"
    )

    print(
        testo[:3000]
    )

    print(
        "\nLINK POTENZIALMENTE UTILI:\n"
    )

    links_trovati = []

    for elemento in soup.find_all(
        "a"
    ):

        href = elemento.get(
            "href"
        )

        titolo = elemento.get_text(
            " ",
            strip=True
        )

        if not href:

            continue

        link_completo = urljoin(
            BASE_URL,
            href
        )

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
    "\n=== TEST MONITOR TOR VERGATA I FASCIA ===\n"
)

for pagina in PAGINE_I_FASCIA:

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
    "\n=== FINE TEST TOR VERGATA ===\n"
)
