import json
import os
import re
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://web.uniroma2.it"

FILE_STORICO = "storico_torvergata.json"

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
            "- Chiamata per mobilità"
        ),
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure-art-7-comma-5-bis-e-comma-5-ter-"
            "cd-chiamata-per-mobilit"
        )
    },
    {
        "nome": "Art. 18, comma 1",
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_art__18__comma_1"
        )
    },
    {
        "nome": "Art. 18, comma 4",
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_art__18__comma_4"
        )
    },
    {
        "nome": "Art. 18, comma 4-ter",
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure-art-18-comma-4ter"
        )
    },
    {
        "nome": "Art. 24, comma 6",
        "url": (
            "https://web.uniroma2.it/it/percorso/"
            "ufficio_concorsi/sezione/"
            "procedure_valutative_art__24__comma_6"
        )
    }
]


KEYWORDS_AREA = [
    "meds-",
    "medf-",
    "bios-",
    "mvet-",
    "iinf-",
    "phys-",
    "bio/",
    "med/",
    "vet/",
    "fis/",
    "ing-inf/",
    "biologia",
    "biomedicina",
    "medicina",
    "scienze cliniche",
    "scienze chirurgiche",
    "chirurgia",
    "anatomia",
    "patologia",
    "oncologia",
    "fisiologia",
    "biochimica",
    "microbiologia",
    "immunologia",
    "odontoiatria"
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
                "Formato dello storico non valido"
            )

        if "bandi_gia_segnalati" not in storico:

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


def invia_email(
    bandi_nuovi
):

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
            "Sono state individuate nuove procedure "
            "di I fascia ancora aperte e appartenenti "
            "alle aree di interesse."
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

    return link.split(
        "#"
    )[0]


def contiene_area_interesse(
    testo
):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in KEYWORDS_AREA
    )


def e_procedura_prima_fascia(
    titolo
):

    titolo_lower = titolo.lower()

    indicatori = [
        "prima fascia",
        "i fascia",
        "professore universitario di ruolo di prima fascia",
        "professore universitario di prima fascia"
    ]

    return any(
        indicatore in titolo_lower
        for indicatore in indicatori
    )


def estrai_data_scadenza(
    testo
):

    pattern = re.compile(
        r"scadenza\s+"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    corrispondenza = pattern.search(
        testo
    )

    if not corrispondenza:

        return None, "Scadenza non individuata"

    data_testo = corrispondenza.group(
        1
    )

    try:

        data_scadenza = datetime.strptime(
            data_testo,
            "%d/%m/%Y"
        ).date()

    except ValueError:

        return None, data_testo

    return (
        data_scadenza,
        data_testo
    )


def trova_contenitore_procedura(
    elemento_link
):

    nodo = elemento_link

    for _ in range(8):

        if nodo is None:

            break

        testo_nodo = nodo.get_text(
            " ",
            strip=True
        )

        testo_lower = testo_nodo.lower()

        if (
            "scadenza" in testo_lower
            and (
                "prima fascia" in testo_lower
                or "professore universitario" in testo_lower
            )
        ):

            return nodo

        nodo = nodo.parent

    return elemento_link.parent


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

        link_completo = normalizza_link(
            href
        )

        if (
            "/it/contenuto/" not in link_completo
        ):

            continue

        if link_completo in links_visti:

            continue

        if not e_procedura_prima_fascia(
            titolo
        ):

            continue

        contenitore = trova_contenitore_procedura(
            elemento
        )

        testo_completo = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True
            )
        )

        if not contiene_area_interesse(
            titolo + " " + testo_completo
        ):

            continue

        data_scadenza, scadenza_testo = (
            estrai_data_scadenza(
                testo_completo
            )
        )

        links_visti.add(
            link_completo
        )

        procedure.append(
            {
                "sezione": nome_sezione,
                "titolo": titolo,
                "link": link_completo,
                "data_scadenza": data_scadenza,
                "scadenza_testo": scadenza_testo
            }
        )

    return procedure


def procedura_ancora_aperta(
    procedura
):

    data_scadenza = procedura[
        "data_scadenza"
    ]

    if data_scadenza is None:

        print(
            "SCADENZA NON INDIVIDUATA, "
            "procedura ignorata:",
            procedura["link"]
        )

        return False

    return data_scadenza >= date.today()


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
                "Procedure di area trovate:",
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

procedure_aperte = []

for procedura in procedure:

    if procedura_ancora_aperta(
        procedura
    ):

        procedure_aperte.append(
            procedura
        )


procedure_uniche = {}

for procedura in procedure_aperte:

    procedure_uniche[
        procedura["link"]
    ] = procedura


procedure_aperte = list(
    procedure_uniche.values()
)


bandi_nuovi = []

for procedura in procedure_aperte:

    if procedura["link"] not in gia_segnalati:

        bandi_nuovi.append(
            procedura
        )


print(
    "\nProcedure aperte di interesse:",
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
