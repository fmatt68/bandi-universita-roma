import requests

from bs4 import BeautifulSoup


URL_TORVERGATA = (
    "http://concorsi.uniroma2.it/it/percorso/"
    "ufficio_concorsi/sezione/procedure_personale_docente"
)


def scarica_pagina():

    risposta = requests.get(
        URL_TORVERGATA,
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

    return risposta.text


def analizza_pagina(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    testo = soup.get_text(
        "\n",
        strip=True
    )

    print(
        "\n=== TESTO TOR VERGATA ===\n"
    )

    print(
        testo[:5000]
    )

    print(
        "\n=== LINK TROVATI ===\n"
    )

    links = []

    for elemento in soup.find_all("a"):

        href = elemento.get(
            "href"
        )

        titolo = elemento.get_text(
            " ",
            strip=True
        )

        if not href:
            continue

        if href not in links:

            links.append(
                href
            )

            print(
                "TITOLO:",
                titolo
            )

            print(
                "LINK:",
                href
            )

            print()


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== TEST MONITOR TOR VERGATA ===\n"
)

html = scarica_pagina()

analizza_pagina(
    html
)

print(
    "\n=== FINE TEST TOR VERGATA ===\n"
)
