import json
import os
import smtplib
import requests

from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from urllib.parse import urljoin


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

KEYWORDS_TRIGGER = [

    "prima fascia",

    "manifestazione di interesse",

    "manifestazioni di interesse",

    "insegnamento a contratto",

    "insegnamenti a contratto",

    "docenza a contratto",

    "docenze a contratto"
]

KEYWORDS_SSD = [

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

    except Exception:

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

    if not EMAIL_PASSWORD:

        print(
            "EMAIL_PASSWORD NON CONFIGURATA"
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


def normalizza_link(href):

    link_assoluto = urljoin(
        URL_UNICAMILLUS,
        href
    )

    link_pulito = link_assoluto.split(
        "?"
    )[0]

    return link_pulito


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

        href_lower = href.lower()

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
                and "chiusura" not in href_lower
                and "proroga" not in href_lower
                and "candidati" not in href_lower
            ):

                link_pulito = normalizza_link(
                    href
                )

                if link_pulito not in links:

                    links.append(
                        link_pulito
                    )

    return (
        sezione_testo,
        links
    )


def analizza_bando(sezione):

    testo = sezione.lower()

    trigger_trovati = []

    ssd_trovati = []

    for parola in KEYWORDS_TRIGGER:

        if parola in testo:

            trigger_trovati.append(
                parola
            )

    for parola in KEYWORDS_SSD:

        if parola in testo:

            ssd_trovati.append(
                parola
            )

    return (
        trigger_trovati,
        ssd_trovati
    )


def filtra_links_interessanti(
    links_bandi,
    trigger_trovati
):

    links_interessanti = []

    trigger_contratti = [
        "manifestazione di interesse",
        "manifestazioni di interesse",
        "insegnamento a contratto",
        "insegnamenti a contratto",
        "docenza a contratto",
        "docenze a contratto"
    ]

    ha_trigger_contratti = any(
        trigger in trigger_contratti
        for trigger in trigger_trovati
    )

    ha_trigger_prima_fascia = (
        "prima fascia" in trigger_trovati
    )

    for link in links_bandi:

        link_lower = link.lower()

        if ha_trigger_contratti:

            if (
                "manifestazione" in link_lower
                or "contratto" in link_lower
                or "docenti-a-contratto" in link_lower
                or "incarichi-docenti" in link_lower
                or "incarichi" in link_lower
                or "lista_idonei" in link_lower
                or "lista-idonei" in link_lower
                or "aggiornamento_lista_idonei" in link_lower
                or "aggiornamento-lista-idonei" in link_lower
            ):

                links_interessanti.append(
                    link
                )

        elif ha_trigger_prima_fascia:

            if (
                "i-fascia" in link_lower
                or "prima-fascia" in link_lower
                or "prima_fascia" in link_lower
            ):

                links_interessanti.append(
                    link
                )

    return links_interessanti


def crea_messaggio_email(
    trigger_trovati,
    ssd_trovati,
    links_nuovi
):

    messaggio = (
        "Nuovi bandi UniCamillus trovati\n\n"
    )

    messaggio += (
        "TRIGGER TROVATI\n"
        "---------------\n"
    )

    for parola in trigger_trovati:

        messaggio += (
            f"- {parola}\n"
        )

    if ssd_trovati:

        messaggio += (
            "\nSSD/PAROLE DI AREA TROVATI\n"
            "--------------------------\n"
        )

        for parola in ssd_trovati:

            messaggio += (
                f"- {parola}\n"
            )

    messaggio += (
        "\nLINK NUOVI SEGNALATI\n"
        "--------------------\n"
    )

    for link in links_nuovi:

        messaggio += (
            f"{link}\n"
        )

    return messaggio


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== MONITOR UNICAMILLUS ===\n"
)

storico = carica_storico()

gia_segnalati = set(
    storico.get(
        "bandi_gia_segnalati",
        []
    )
)

html = scarica_pagina()

sezione_bandi, links_bandi = (
    estrai_bandi_aperti(
        html
    )
)

trigger_trovati, ssd_trovati = (
    analizza_bando(
        sezione_bandi
    )
)

if not trigger_trovati:

    print(
        "NESSUN BANDO DI INTERESSE"
    )

else:

    print(
        "BANDI DI INTERESSE RILEVATI\n"
    )

    for parola in trigger_trovati:

        print(
            f"TRIGGER: {parola}"
        )

    for parola in ssd_trovati:

        print(
            f"SSD: {parola}"
        )

    links_interessanti = filtra_links_interessanti(
        links_bandi,
        trigger_trovati
    )

    print(
        f"LINK INTERESSANTI TROVATI: {len(links_interessanti)}"
    )

    links_nuovi = []

    for link in links_interessanti:

        if link not in gia_segnalati:

            links_nuovi.append(
                link
            )

    if not links_nuovi:

        print(
            "NESSUN NUOVO BANDO"
        )

    else:

        print(
            f"NUOVI LINK DA SEGNALARE: {len(links_nuovi)}"
        )

        messaggio = crea_messaggio_email(
            trigger_trovati,
            ssd_trovati,
            links_nuovi
        )

        invia_email(
            messaggio
        )

        for link in links_nuovi:

            storico[
                "bandi_gia_segnalati"
            ].append(
                link
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
