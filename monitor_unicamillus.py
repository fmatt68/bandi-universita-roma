import json
import os
import smtplib
import requests

from bs4 import BeautifulSoup
from email.mime.text import MIMEText


URL_UNICAMILLUS = (
    "https://unicamillus.org/lavora-con-noi/bandi-docenti/"
)

FILE_STORICO = (
    "storico_unicamillus.json"
)

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)

KEYWORDS_INTERESSE = [
    "insegnamento a contratto",
    "docenza a contratto",
    "insegnamenti a contratto",
    "docenze a contratto",
    "manifestazione di interesse",
    "manifestazioni di interesse",
    "prima fascia",
    "bios-",
    "meds-",
    "iinf-",
    "phys-",
    "odontoiatria",
    "medicina",
    "chirurgia",
    "anatomia",
    "patologia",
    "oncologia"
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


def invia_email(messaggio):

    if not EMAIL_ADDRESS:

        print(
            "EMAIL NON CONFIGURATA"
        )

        return

    email = MIMEText(
        messaggio,
        "plain",
        "utf-8"
    )

    email["Subject"] = (
        "[UNICAMILLUS] Nuovi bandi"
    )

    email["From"] = EMAIL_ADDRESS

    email["To"] = EMAIL_ADDRESS

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL_ADDRESS,
        EMAIL_PASSWORD
    )

    server.send_message(
        email
    )

    server.quit()

    print(
        "EMAIL INVIATA"
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

        return "", []

    if fine == -1:

        fine = len(testo)

    sezione_testo = testo[
        inizio:fine
    ]

    links = []

    for link in soup.find_all("a"):

        href = link.get(
            "href"
        )

        if not href:
            continue

        href_lower = (
            href.lower()
        )

        if (
            "wp-content/uploads" in href_lower
            and (
                "bando" in href_lower
                or "avviso" in href_lower
            )
        ):

            if (
                "verbale" not in href_lower
                and "commissione" not in href_lower
                and "convocazione" not in href_lower
                and "regolarita" not in href_lower
                and "argoment" not in href_lower
                and "allegati" not in href_lower
                and "privacy" not in href_lower
            ):

                if href not in links:

                    links.append(
                        href
                    )

    return (
        sezione_testo,
        links
    )


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

sezione_bandi, links_bandi = (
    estrai_bandi_aperti(
        html
    )
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

    messaggio = (
        "Nuovi bandi UniCamillus trovati\n\n"
    )

    messaggio += (
        "PAROLE CHIAVE TROVATE\n"
        "---------------------\n"
    )

    for parola in parole_trovate:

        messaggio += (
            f"- {parola}\n"
        )

    messaggio += (
        "\nLINK AI BANDI\n"
        "-------------\n"
    )

    for link in links_bandi:

        messaggio += (
            f"{link}\n"
        )

    invia_email(
        messaggio
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
