import requests

from bs4 import BeautifulSoup


URL_UNICAMILLUS = (
    "https://unicamillus.org/lavora-con-noi/bandi-docenti/"
)


KEYWORDS_INTERESSE = [

    "insegnamento a contratto",

    "professore universitario",

    "prima fascia",

    "seconda fascia",

    "bios-",

    "meds-"
]


def scarica_pagina():

    risposta = requests.get(
        URL_UNICAMILLUS,
        timeout=60
    )

    print(
        "Status code:",
        risposta.status_code
    )

    return risposta.text


def estrai_bandi_aperti(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    testo = soup.get_text(
        "\n",
        strip=True
    )

    inizio = testo.find(
        "BANDI APERTI"
    )

    fine = testo.find(
        "BANDI CHIUSI"
    )

    if inizio == -1:

        print(
            "Sezione BANDI APERTI non trovata"
        )

        return ""

    if fine == -1:

        fine = len(testo)

    return testo[
        inizio:fine
    ]


def analizza_bandi(sezione):

    print(
        "\n=== BANDI APERTI UNICAMILLUS ===\n"
    )

    print(
        sezione
    )

    print(
        "\n=== RISULTATO FILTRI ===\n"
    )

    sezione_minuscola = (
        sezione.lower()
    )

    trovate = []

    for parola in KEYWORDS_INTERESSE:

        if parola in sezione_minuscola:

            trovate.append(
                parola
            )

    if trovate:

        for elemento in trovate:

            print(
                f"TROVATO: {elemento}"
            )

    else:

        print(
            "Nessuna keyword trovata"
        )

    print(
        "\n=== FINE ==="
    )


# ==========================================
# MAIN
# ==========================================

html = scarica_pagina()

sezione_bandi = estrai_bandi_aperti(
    html
)

analizza_bandi(
    sezione_bandi
)
