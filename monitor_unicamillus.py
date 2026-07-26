import json
import requests

from bs4 import BeautifulSoup


URL_UNICAMILLUS = (
    "https://unicamillus.org/lavora-con-noi/bandi-docenti/"
)

FILE_STORICO = (
    "storico_unicamillus.json"
)

KEYWORDS_INTERESSE = [

    "insegnamento a contratto",

    "professore universitario",

    "prima fascia",

    "seconda fascia",

    "bios-",

    "meds-"
]


def carica_storico():

    try:

        with open(
            FILE_STORICO,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except:

        return {
            "bandi_gia_segnalati": []
        }


def salva_storico(storico):

    with open(
        FILE_STORICO,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            storico,
            file,
            indent=2,
            ensure_ascii=False
        )


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

        return ""

    if fine == -1:

        fine = len(testo)

    return testo[
        inizio:fine
    ]


def genera_id(sezione):

    righe = []

    for riga in sezione.splitlines():

        riga = riga.strip()

        if not riga:

            continue

        if (
            "Scadenza:" in riga
            or "SSD " in riga
            or "GSD " in riga
        ):

            righe.append(
                riga
            )

    return "|".join(
        righe[:20]
    )


def analizza_bando(sezione):

    sezione_minuscola = (
        sezione.lower()
    )

    trovate = []

    for parola in KEYWORDS_INTERESSE:

        if parola in sezione_minuscola:

            trovate.append(
                parola
            )

    return trovate


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== MONITOR UNICAMILLUS ===\n"
)

storico = carica_storico()

html = scarica_pagina()

sezione_bandi = estrai_bandi_aperti(
    html
)

id_bando = genera_id(
    sezione_bandi
)

if id_bando in storico[
    "bandi_gia_segnalati"
]:

    print(
        "NESSUN NUOVO BANDO"
    )

else:

    parole_trovate = (
        analizza_bando(
            sezione_bandi
        )
    )

    print(
        "NUOVI BANDI APERTI\n"
    )

    for parola in parole_trovate:

        print(
            f"TROVATO: {parola}"
        )

    storico[
        "bandi_gia_segnalati"
    ].append(
        id_bando
    )

    salva_storico(
        storico
    )

    print(
        "\nSTORICO AGGIORNATO"
    )

print(
    "\n=== FINE ==="
)
