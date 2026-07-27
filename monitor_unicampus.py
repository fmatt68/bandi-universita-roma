import json
import os
import re
import smtplib

from datetime import date, datetime
from email.mime.text import MIMEText
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.unicampus.it"

FILE_STORICO = "storico_unicampus.json"

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)


PAGINE_UNICAMPUS = [
    {
        "nome": (
            "Professori I e II fascia "
            "- Procedure selettive"
        ),
        "tipo": "prima_fascia",
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
        "tipo": "prima_fascia",
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "professori-i-e-ii-procedure-valutative/"
        )
    },
    {
        "nome": "Docenti a contratto",
        "tipo": "docenza",
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "docenti-a-contratto/"
        )
    },
    {
        "nome": "Manifestazioni di interesse",
        "tipo": "manifestazione",
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
        "tipo": "manifestazione",
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "manifestazioni-di-interesse-foundation-year/"
        )
    }
]


PATTERN_SETTORI_INTERESSE = [
    r"\b\d{2}/MEDS-\d{2}\b",
    r"\bMEDS-\d{2}/[A-Z]\b",

    r"\b\d{2}/MEDF-\d{2}\b",
    r"\bMEDF-\d{2}/[A-Z]\b",

    r"\b\d{2}/BIOS-\d{2}\b",
    r"\bBIOS-\d{2}/[A-Z]\b",

    r"\b\d{2}/MVET-\d{2}\b",
    r"\bMVET-\d{2}/[A-Z]\b",

    r"\b\d{2}/IINF-\d{2}\b",
    r"\bIINF-\d{2}/[A-Z]\b",

    r"\b\d{2}/PHYS-\d{2}\b",
    r"\bPHYS-\d{2}/[A-Z]\b",

    r"\bBIO/\d{2}\b",
    r"\bMED/\d{2}\b",
    r"\bVET/\d{2}\b",
    r"\bFIS/\d{2}\b",
    r"\bING-INF/\d{2}\b"
]


PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "incarico di didattica",
    "incarichi di didattica",
    "didattica integrativa",
    "attivita didattica",
    "attività didattica",
    "insegnamento a contratto",
    "insegnamenti a contratto",
    "docenza a contratto",
    "docenze a contratto"
]


PAROLE_MANIFESTAZIONE_DIDATTICA = [
    "insegnamento",
    "insegnamenti",
    "didattica",
    "docente",
    "docenti",
    "docenza",
    "foundation year"
]


PAROLE_DA_ESCLUDERE = [
    "commissione",
    "nomina commissione",
    "verbale",
    "approvazione atti",
    "approvazione degli atti",
    "graduatoria",
    "esito",
    "convocazione",
    "rinuncia",
    "chiusura",
    "revoca"
]


MESI_ITALIANI = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12
}


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

    risposta.raise_for_status()

    print(
        "Pagina letta:",
        risposta.url
    )

    return risposta.text


def normalizza_testo(testo):

    return " ".join(
        unescape(
            testo
        ).split()
    )


def normalizza_link(href):

    link = unescape(
        href
    )

    link = link.replace(
        "\\/",
        "/"
    )

    link = urljoin(
        BASE_URL,
        link
    )

    parti = urlsplit(
        link
    )

    link = urlunsplit(
        (
            parti.scheme,
            parti.netloc,
            parti.path,
            "",
            ""
        )
    )

    if not link.endswith(
        "/"
    ):

        link += "/"

    return link


def titolo_da_escludere(titolo):

    titolo_lower = titolo.lower()

    return any(
        parola in titolo_lower
        for parola in PAROLE_DA_ESCLUDERE
    )


def e_prima_fascia(titolo):

    titolo_lower = titolo.lower()

    if titolo_da_escludere(
        titolo
    ):

        return False

    indicatori_seconda_fascia = [
        "ii fascia",
        "seconda fascia",
        "val-ass",
        "codice concorso ass/"
    ]

    if any(
        indicatore in titolo_lower
        for indicatore in indicatori_seconda_fascia
    ):

        return False

    indicatori_prima_fascia = [
        "i fascia",
        "prima fascia",
        "selettiva-i-fascia",
        "valutativa-i-fascia",
        "val-ord",
        "codice concorso ord/"
    ]

    return any(
        indicatore in titolo_lower
        for indicatore in indicatori_prima_fascia
    )


def e_docenza_contratto(titolo):

    titolo_lower = titolo.lower()

    if titolo_da_escludere(
        titolo
    ):

        return False

    return any(
        parola in titolo_lower
        for parola in PAROLE_DOCENZA
    )


def e_manifestazione_didattica(titolo):

    titolo_lower = titolo.lower()

    if titolo_da_escludere(
        titolo
    ):

        return False

    if (
        "manifestazione" not in titolo_lower
        and "riapertura termini" not in titolo_lower
    ):

        return False

    return any(
        parola in titolo_lower
        for parola in PAROLE_MANIFESTAZIONE_DIDATTICA
    )


def contiene_settore_interesse(testo):

    testo_maiuscolo = testo.upper()

    return any(
        re.search(
            pattern,
            testo_maiuscolo
        )
        for pattern in PATTERN_SETTORI_INTERESSE
    )


def estrai_codici_area(testo):

    testo_maiuscolo = testo.upper()

    codici = []

    for pattern in PATTERN_SETTORI_INTERESSE:

        risultati = re.findall(
            pattern,
            testo_maiuscolo
        )

        for codice in risultati:

            if codice not in codici:

                codici.append(
                    codice
                )

    return codici


def trova_titolo_link(elemento):

    titolo = normalizza_testo(
        elemento.get_text(
            " ",
            strip=True
        )
    )

    if titolo:

        return titolo

    contenitore = elemento.find_parent(
        "div",
        class_=lambda classi: (
            classi
            and "news-list" in " ".join(
                classi
                if isinstance(
                    classi,
                    list
                )
                else [classi]
            )
        )
    )

    if contenitore is None:

        return ""

    selettori = [
        ".title-rep",
        ".news-card-link",
        "h2",
        "h3",
        "h4"
    ]

    for selettore in selettori:

        nodo_titolo = contenitore.select_one(
            selettore
        )

        if nodo_titolo is None:

            continue

        titolo = normalizza_testo(
            nodo_titolo.get_text(
                " ",
                strip=True
            )
        )

        if titolo:

            return titolo

    return ""


def estrai_link_concorso(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    risultati = {}

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        href = elemento.get(
            "href"
        )

        if not href:

            continue

        if "/concorso/" not in href.lower():

            continue

        link = normalizza_link(
            href
        )

        titolo = trova_titolo_link(
            elemento
        )

        if not titolo:

            continue

        if (
            link not in risultati
            or len(titolo) > len(
                risultati[link]
            )
        ):

            risultati[
                link
            ] = titolo

    return [
        {
            "link": link,
            "titolo": titolo
        }
        for link, titolo in risultati.items()
    ]


def estrai_date_numeriche(testo):

    pattern = re.compile(
        r"\b(\d{1,2})\d{1,2}\d{4}\b"
    )

    date_trovate = []

    for giorno, mese, anno in pattern.findall(
        testo
    ):

        try:

            data = date(
                int(anno),
                int(mese),
                int(giorno)
            )

            if data not in date_trovate:

                date_trovate.append(
                    data
                )

        except ValueError:

            continue

    return date_trovate


def estrai_date_testuali(testo):

    pattern = re.compile(
        r"\b(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|"
        r"luglio|agosto|settembre|ottobre|novembre|dicembre)"
        r"\s+(\d{4})\b",
        re.IGNORECASE
    )

    date_trovate = []

    for giorno, mese_testo, anno in pattern.findall(
        testo
    ):

        mese = MESI_ITALIANI.get(
            mese_testo.lower()
        )

        if mese is None:

            continue

        try:

            data = date(
                int(anno),
                mese,
                int(giorno)
            )

            if data not in date_trovate:

                date_trovate.append(
                    data
                )

        except ValueError:

            continue

    return date_trovate


def estrai_scadenza(testo):

    testo_normalizzato = normalizza_testo(
        testo
    )

    pattern_blocchi = [
        re.compile(
            r"scadenza[^.]{0,180}",
            re.IGNORECASE
        ),
        re.compile(
            r"termine[^.]{0,180}",
            re.IGNORECASE
        ),
        re.compile(
            r"presentazione\s+(?:online\s+)?"
            r"(?:della\s+)?domanda[^.]{0,250}",
            re.IGNORECASE
        )
    ]

    date_candidate = []

    for pattern in pattern_blocchi:

        for corrispondenza in pattern.findall(
            testo_normalizzato
        ):

            date_candidate.extend(
                estrai_date_numeriche(
                    corrispondenza
                )
            )

            date_candidate.extend(
                estrai_date_testuali(
                    corrispondenza
                )
            )

    if not date_candidate:

        return (
            None,
            "Scadenza non individuata"
        )

    date_future = [
        data
        for data in date_candidate
        if data >= date.today()
    ]

    if date_future:

        data_scadenza = min(
            date_future
        )

    else:

        data_scadenza = max(
            date_candidate
        )

    return (
        data_scadenza,
        data_scadenza.strftime(
            "%d/%m/%Y"
        )
    )


def estrai_dettaglio_concorso(
    sessione,
    candidato
):

    try:

        html = scarica_pagina(
            sessione,
            candidato["link"]
        )

    except Exception as errore:

        print(
            "ERRORE NEL DETTAGLIO:",
            candidato["link"]
        )

        print(
            str(
                errore
            )
        )

        return None

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

    titolo_pagina = candidato[
        "titolo"
    ]

    intestazione = soup.find(
        ["h1", "h2"]
    )

    if intestazione is not None:

        titolo_intestazione = normalizza_testo(
            intestazione.get_text(
                " ",
                strip=True
            )
        )

        if (
            titolo_intestazione
            and len(
                titolo_intestazione
            ) > len(
                titolo_pagina
            )
        ):

            titolo_pagina = titolo_intestazione

    data_scadenza, scadenza_testo = (
        estrai_scadenza(
            testo
        )
    )

    codici_area = estrai_codici_area(
        titolo_pagina
        + " "
        + testo
    )

    return {
        "sezione": candidato["sezione"],
        "tipo": candidato["tipo"],
        "titolo": titolo_pagina,
        "link": candidato["link"],
        "codici_area": codici_area,
        "data_scadenza": data_scadenza,
        "scadenza_testo": scadenza_testo
    }


def candidato_ammesso(
    tipo,
    titolo,
    link
):

    testo_completo = (
        titolo
        + " "
        + link.replace(
            "-",
            " "
        )
    )

    if tipo == "prima_fascia":

        return (
            e_prima_fascia(
                testo_completo
            )
            and contiene_settore_interesse(
                testo_completo
            )
        )

    if tipo == "docenza":

        return e_docenza_contratto(
            testo_completo
        )

    if tipo == "manifestazione":

        return e_manifestazione_didattica(
            testo_completo
        )

    return False


def raccogli_candidati(
    sessione
):

    candidati = {}

    for pagina in PAGINE_UNICAMPUS:

        print(
            "\nControllo sezione:",
            pagina["nome"]
        )

        try:

            html = scarica_pagina(
                sessione,
                pagina["url"]
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

            continue

        links = estrai_link_concorso(
            html
        )

        trovati = 0

        for elemento in links:

            titolo = elemento[
                "titolo"
            ]

            link = elemento[
                "link"
            ]

            if not candidato_ammesso(
                pagina["tipo"],
                titolo,
                link
            ):

                continue

            candidati[
                link
            ] = {
                "sezione": pagina["nome"],
                "tipo": pagina["tipo"],
                "titolo": titolo,
                "link": link
            }

            trovati += 1

        print(
            "Candidati pertinenti trovati:",
            trovati
        )

    return list(
        candidati.values()
    )


def dettaglio_ammesso(
    dettaglio
):

    titolo = dettaglio[
        "titolo"
    ]

    testo_completo = (
        titolo
        + " "
        + dettaglio["link"].replace(
            "-",
            " "
        )
    )

    if titolo_da_escludere(
        titolo
    ):

        return False

    if dettaglio["tipo"] == "prima_fascia":

        return (
            e_prima_fascia(
                testo_completo
            )
            and contiene_settore_interesse(
                testo_completo
            )
        )

    if dettaglio["tipo"] == "docenza":

        return e_docenza_contratto(
            testo_completo
        )

    if dettaglio["tipo"] == "manifestazione":

        return e_manifestazione_didattica(
            testo_completo
        )

    return False


def procedura_aperta(
    dettaglio
):

    data_scadenza = dettaglio[
        "data_scadenza"
    ]

    if data_scadenza is None:

        print(
            "IGNORATA: scadenza non individuata:",
            dettaglio["link"]
        )

        return False

    return data_scadenza >= date.today()


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
        "Nuovi bandi Campus Bio-Medico trovati",
        "",
        (
            "Nuove procedure ancora aperte "
            "e corrispondenti ai criteri di interesse:"
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
        "[CAMPUS BIO-MEDICO] Nuovi bandi"
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
    "\n=== MONITOR CAMPUS BIO-MEDICO ===\n"
)

sessione = crea_sessione()

storico = carica_storico()

gia_segnalati = set(
    storico.get(
        "bandi_gia_segnalati",
        []
    )
)

candidati = raccogli_candidati(
    sessione
)

print(
    "\nCandidati complessivi:",
    len(candidati)
)

procedure_aperte = []

for candidato in candidati:

    dettaglio = estrai_dettaglio_concorso(
        sessione,
        candidato
    )

    if dettaglio is None:

        continue

    if not dettaglio_ammesso(
        dettaglio
    ):

        continue

    if not procedura_aperta(
        dettaglio
    ):

        continue

    procedure_aperte.append(
        dettaglio
    )


procedure_uniche = {}

for procedura in procedure_aperte:

    procedure_uniche[
        procedura["link"]
    ] = procedura


procedure_aperte = list(
    procedure_uniche.values()
)


procedure_aperte.sort(
    key=lambda elemento: (
        elemento["data_scadenza"],
        elemento["titolo"]
    )
)


bandi_nuovi = [
    procedura
    for procedura in procedure_aperte
    if procedura["link"] not in gia_segnalati
]


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

        if bando["codici_area"]:

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
            "\nSTORICO CAMPUS BIO-MEDICO AGGIORNATO"
        )

    else:

        print(
            "Storico non aggiornato perché "
            "l'email non è stata inviata"
        )


print(
    "\n=== FINE MONITOR CAMPUS BIO-MEDICO ==="
)
