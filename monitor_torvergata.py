import json
import os
import re
import smtplib

from datetime import date, datetime
from email.mime.text import MIMEText
from urllib.parse import urljoin

import requests

from bs4 import BeautifulSoup


BASE_URL = (
    "https://web.uniroma2.it"
)

FILE_STORICO = (
    "storico_torvergata.json"
)

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
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


INIZI_TITOLO_AMMESSI = [
    "procedura comparativa",
    "procedura valutativa",
    "procedura per",
    "avviso pubblico"
]


PAROLE_DA_ESCLUDERE = [
    "commissione esaminatrice",
    "nomina commissione",
    "decreto di nomina",
    "approvazione atti",
    "regolarita degli atti",
    "regolarità degli atti",
    "verbale",
    "convocazione",
    "esito",
    "graduatoria",
    "rinuncia",
    "chiusura",
    "proroga commissione"
]


PATTERN_SETTORI_INTERESSE = [
    r"\b\d{2}/meds-\d{2}\b",
    r"\bmeds-\d{2}/[a-z]\b",

    r"\b\d{2}/medf-\d{2}\b",
    r"\bmedf-\d{2}/[a-z]\b",

    r"\b\d{2}/bios-\d{2}\b",
    r"\bbios-\d{2}/[a-z]\b",

    r"\b\d{2}/mvet-\d{2}\b",
    r"\bmvet-\d{2}/[a-z]\b",

    r"\b\d{2}/iinf-\d{2}\b",
    r"\biinf-\d{2}/[a-z]\b",

    r"\b\d{2}/phys-\d{2}\b",
    r"\bphys-\d{2}/[a-z]\b",

    r"\bbio/\d{2}\b",
    r"\bmed/\d{2}\b",
    r"\bvet/\d{2}\b",
    r"\bfis/\d{2}\b",
    r"\bing-inf/\d{2}\b"
]


def carica_storico():

    try:

        with open(
            FILE_STORICO,
            "r",
            encoding="utf-8"
        ) as file:

            storico = json.load(
                file
            )

        if not isinstance(
            storico,
            dict
        ):

            raise ValueError(
                "Formato storico non valido"
            )

        bandi = storico.get(
            "bandi_gia_segnalati"
        )

        if not isinstance(
            bandi,
            list
        ):

            storico[
                "bandi_gia_segnalati"
            ] = []

        return storico

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ):

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

    risposta.raise_for_status()

    print(
        "Pagina letta:",
        risposta.url
    )

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


def titolo_da_escludere(titolo):

    titolo_lower = titolo.lower()

    return any(
        parola in titolo_lower
        for parola in PAROLE_DA_ESCLUDERE
    )


def e_titolo_di_procedura(titolo):

    titolo_lower = titolo.lower()

    if titolo_da_escludere(
        titolo
    ):

        return False

    if not any(
        titolo_lower.startswith(
            inizio
        )
        for inizio in INIZI_TITOLO_AMMESSI
    ):

        return False

    indicatori_prima_fascia = [
        "prima fascia",
        " i fascia",
        "professore universitario di ruolo di prima fascia",
        "professore universitario di prima fascia"
    ]

    return any(
        indicatore in titolo_lower
        for indicatore in indicatori_prima_fascia
    )


def contiene_area_interesse(testo):

    testo_lower = testo.lower()

    return any(
        re.search(
            pattern,
            testo_lower
        )
        for pattern in PATTERN_SETTORI_INTERESSE
    )


def estrai_codici_area(testo):

    testo_lower = testo.lower()

    codici = []

    for pattern in PATTERN_SETTORI_INTERESSE:

        corrispondenze = re.findall(
            pattern,
            testo_lower
        )

        for codice in corrispondenze:

            codice_maiuscolo = codice.upper()

            if codice_maiuscolo not in codici:

                codici.append(
                    codice_maiuscolo
                )

    return codici


def estrai_data_scadenza(testo):

    pattern_scadenza = re.compile(
        r"scadenza\s*"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    corrispondenze = pattern_scadenza.findall(
        testo
    )

    if not corrispondenze:

        return (
            None,
            "Scadenza non individuata"
        )

    date_valide = []

    for data_testo in corrispondenze:

        try:

            data_scadenza = datetime.strptime(
                data_testo,
                "%d/%m/%Y"
            ).date()

            date_valide.append(
                (
                    data_scadenza,
                    data_testo
                )
            )

        except ValueError:

            continue

    if not date_valide:

        return (
            None,
            "Scadenza non individuata"
        )

    data_scadenza, data_testo = max(
        date_valide,
        key=lambda elemento: elemento[0]
    )

    return (
        data_scadenza,
        data_testo
    )


def trova_riga_procedura(elemento):

    riga = elemento.find_parent(
        "tr"
    )

    if riga is not None:

        testo_riga = normalizza_testo(
            riga.get_text(
                " ",
                strip=True
            )
        )

        if "scadenza" in testo_riga.lower():

            return riga

    selettori = [
        "views-row",
        "view-row",
        "item-list",
        "card",
        "row"
    ]

    nodo = elemento.parent

    for _ in range(6):

        if nodo is None:

            break

        classi = nodo.get(
            "class",
            []
        )

        classi_testo = " ".join(
            classi
        ).lower()

        testo_nodo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        if (
            any(
                selettore in classi_testo
                for selettore in selettori
            )
            and "scadenza" in testo_nodo.lower()
            and len(testo_nodo) < 5000
        ):

            return nodo

        nodo = nodo.parent

    return None


def estrai_scadenza_da_dettaglio(url):

    try:

        html = scarica_pagina(
            url
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        testo = normalizza_testo(
            soup.get_text(
                " ",
                strip=True
            )
        )

        return estrai_data_scadenza(
            testo
        )

    except Exception as errore:

        print(
            "Impossibile leggere il dettaglio:",
            url
        )

        print(
            str(
                errore
            )
        )

        return (
            None,
            "Scadenza non individuata"
        )


def estrai_procedure_da_pagina(
    nome_sezione,
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    procedure = []

    links_visti = set()

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

        if not titolo:

            continue

        link = normalizza_link(
            href
        )

        if (
            "/it/contenuto/" not in link
        ):

            continue

        if link in links_visti:

            continue

        if not e_titolo_di_procedura(
            titolo
        ):

            continue

        if not contiene_area_interesse(
            titolo
        ):

            continue

        codici_area = estrai_codici_area(
            titolo
        )

        riga = trova_riga_procedura(
            elemento
        )

        if riga is not None:

            testo_riga = normalizza_testo(
                riga.get_text(
                    " ",
                    strip=True
                )
            )

            data_scadenza, scadenza_testo = (
                estrai_data_scadenza(
                    testo_riga
                )
            )

        else:

            data_scadenza = None

            scadenza_testo = (
                "Scadenza non individuata"
            )

        if data_scadenza is None:

            print(
                "Scadenza non trovata nella riga, "
                "apro il dettaglio:",
                link
            )

            data_scadenza, scadenza_testo = (
                estrai_scadenza_da_dettaglio(
                    link
                )
            )

        links_visti.add(
            link
        )

        procedure.append(
            {
                "sezione": nome_sezione,
                "titolo": titolo,
                "link": link,
                "codici_area": codici_area,
                "data_scadenza": data_scadenza,
                "scadenza_testo": scadenza_testo
            }
        )

    return procedure


def procedura_ancora_aperta(procedura):

    data_scadenza = procedura[
        "data_scadenza"
    ]

    if data_scadenza is None:

        print(
            "IGNORATA: scadenza non individuata:",
            procedura["link"]
        )

        return False

    if data_scadenza < date.today():

        return False

    return True


def raccogli_procedure():

    tutte_le_procedure = []

    for pagina in PAGINE_I_FASCIA:

        print(
            "\nControllo sezione:",
            pagina["nome"]
        )

        try:

            html = scarica_pagina(
                pagina["url"]
            )

            procedure = estrai_procedure_da_pagina(
                pagina["nome"],
                html
            )

            print(
                "Procedure pertinenti trovate:",
                len(procedure)
            )

            tutte_le_procedure.extend(
                procedure
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

    return tutte_le_procedure


def invia_email(bandi_nuovi):

    if not EMAIL_ADDRESS:

        print(
            "EMAIL NON CONFIGURATA"
        )

        return False

    if not EMAIL_PASSWORD:

        print(
            "EMAIL_PASSWORD NON CONFIGURATA"
        )

        return False

    righe = [
        "Nuovi bandi Tor Vergata trovati",
        "",
        (
            "Nuove procedure di I fascia, "
            "ancora aperte e appartenenti "
            "alle aree disciplinari di interesse:"
        ),
        ""
    ]

    for numero, bando in enumerate(
        bandi_nuovi,
        start=1
    ):

        righe.append(
            "========================================"
        )

        righe.append(
            f"BANDO {numero}"
        )

        righe.append(
            "========================================"
        )

        righe.append(
            f"Sezione: {bando['sezione']}"
        )

        righe.append(
            f"Scadenza: {bando['scadenza_testo']}"
        )

        if bando["codici_area"]:

            righe.append(
                "Area: "
                + ", ".join(
                    bando["codici_area"]
                )
            )

        righe.append("")

        righe.append(
            bando["titolo"]
        )

        righe.append("")

        righe.append(
            "Link alla procedura:"
        )

        righe.append(
            bando["link"]
        )

        righe.append("")

    messaggio = "\n".join(
        righe
    )

    email = MIMEText(
        messaggio,
        "plain",
        "utf-8"
    )

    email["Subject"] = (
        "[TOR VERGATA] Nuovi bandi di I fascia"
    )

    email["From"] = EMAIL_ADDRESS

    email["To"] = EMAIL_ADDRESS

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=60
    )

    try:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(
            email
        )

    finally:

        server.quit()

    print(
        "EMAIL INVIATA"
    )

    return True


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== MONITOR TOR VERGATA ===\n"
)

storico = carica_storico()

gia_segnalati = set(
    storico.get(
        "bandi_gia_segnalati",
        []
    )
)

procedure = raccogli_procedure()


procedure_uniche = {}

for procedura in procedure:

    procedure_uniche[
        procedura["link"]
    ] = procedura


procedure = list(
    procedure_uniche.values()
)


procedure_aperte = []

for procedura in procedure:

    if procedura_ancora_aperta(
        procedura
    ):

        procedure_aperte.append(
            procedura
        )


procedure_aperte.sort(
    key=lambda elemento: (
        elemento["data_scadenza"],
        elemento["titolo"]
    )
)


bandi_nuovi = []

for procedura in procedure_aperte:

    if procedura["link"] not in gia_segnalati:

        bandi_nuovi.append(
            procedura
        )


print(
    "\nProcedure pertinenti complessive:",
    len(procedure)
)

print(
    "Procedure aperte di interesse:",
    len(procedure_aperte)
)

print(
    "Nuove procedure da segnalare:",
    len(bandi_nuovi)
)


if not bandi_nuovi:

    print(
        "NESSUN NUOVO BANDO"
    )

else:

    for bando in bandi_nuovi:

        print(
            "\nNUOVO BANDO:"
        )

        print(
            bando["titolo"]
        )

        print(
            "Area:",
            ", ".join(
                bando["codici_area"]
            )
        )

        print(
            "Scadenza:",
            bando["scadenza_testo"]
        )

        print(
            "Link:",
            bando["link"]
        )

    email_inviata = invia_email(
        bandi_nuovi
    )

    if email_inviata:

        for bando in bandi_nuovi:

            storico[
                "bandi_gia_segnalati"
            ].append(
                bando["link"]
            )

        salva_storico(
            storico
        )

        print(
            "\nSTORICO TOR VERGATA AGGIORNATO"
        )

    else:

        print(
            "Storico non aggiornato perché "
            "l'email non è stata inviata"
        )


print(
    "\n=== FINE MONITOR TOR VERGATA ==="
)
