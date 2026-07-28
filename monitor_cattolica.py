import json
import os
import re
import smtplib

from datetime import date, datetime
from email.mime.text import MIMEText
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


BASE_URL = "https://progetti.unicatt.it"

URL_INDICE_ROMA = (
    "https://progetti.unicatt.it/"
    "progetti-ateneo-concorsi-roma"
)

FILE_STORICO = "storico_cattolica.json"

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)


PAGINE_PRIMA_FASCIA = [
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 18"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-di-professori-"
            "di-prima-e-seconda-fascia-legge-240-2010-art-18"
        )
    },
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 7, commi 5-bis e 5-ter"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-di-professori-"
            "di-prima-e-seconda-fascia-legge-240-2010-art-7"
        )
    },
    {
        "nome": (
            "Professori I e II fascia "
            "- Art. 24, comma 6"
        ),
        "tipo": "prima_fascia",
        "url": (
            "https://progetti.unicatt.it/"
            "progetti-ateneo-roma-chiamata-diretta-di-"
            "professore-di-i-e-ii-fascia-legge-240-2010-"
            "art-24-comma-6"
        )
    }
]


PAROLE_PAGINA_DOCENZA = [
    "conferimento insegnamenti",
    "conferimento di insegnamenti",
    "incarichi di insegnamento",
    "incarico di insegnamento",
    "docenti a contratto",
    "docente a contratto",
    "professore a contratto",
    "professori a contratto",
    "copertura discipline"
]


PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore universitario di prima fascia",
    "professore di ruolo di prima fascia",
    "professori di ruolo di prima fascia",
    "posto di professore di ruolo di prima fascia",
    "posti di professore di ruolo di prima fascia"
]


PAROLE_SECONDA_FASCIA = [
    "seconda fascia",
    "ii fascia",
    "professore universitario di seconda fascia",
    "professore di ruolo di seconda fascia",
    "professori di ruolo di seconda fascia"
]


PAROLE_DOCENZA_CONTRATTO = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "professore a contratto",
    "professori a contratto",
    "insegnamento a contratto",
    "insegnamenti a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento di insegnamento",
    "conferimento di insegnamenti",
    "conferimento insegnamento",
    "conferimento insegnamenti",
    "contratto di insegnamento",
    "contratti di insegnamento",
    "incarico di docenza",
    "incarichi di docenza",
    "didattica integrativa",
    "attivita didattica",
    "attività didattica",
    "scuola di specializzazione",
    "scuole di specializzazione"
]


PAROLE_DOCUMENTO_PRINCIPALE = [
    "bando",
    "procedura di valutazione",
    "procedura selettiva",
    "decreto rettorale",
    "decreto rettorale n.",
    "avviso di selezione",
    "selezione per titoli"
]


PAROLE_DOCUMENTO_ACCESSORIO = [
    "domanda di incarico",
    "domanda di ammissione",
    "allegato",
    "elenco discipline",
    "indicatori anvur",
    "modulo",
    "fac-simile",
    "fac simile",
    "informativa privacy",
    "regolamento",
    "disposizioni operative"
]


PAROLE_DA_ESCLUDERE = [
    "commissione",
    "nomina commissione",
    "verbale",
    "approvazione atti",
    "approvazione degli atti",
    "graduatoria",
    "esito",
    "rinuncia",
    "revoca",
    "procedura conclusa",
    "procedura chiusa"
]


PREFISSI_AREA_INTERESSE = [
    "MEDS",
    "MEDF",
    "BIOS",
    "MVET",
    "IINF",
    "PHYS",
    "IBIO",
    "BIO",
    "MED",
    "VET",
    "FIS",
    "ING-INF"
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
        testo.split()
    )


def normalizza_link(href):

    link = urljoin(
        BASE_URL,
        href
    )

    parti = urlsplit(
        link
    )

    return urlunsplit(
        (
            parti.scheme,
            parti.netloc,
            parti.path,
            parti.query,
            ""
        )
    )


def testo_link_decodificato(link):

    return unquote(
        link
    ).replace(
        "-",
        " "
    ).replace(
        "_",
        " "
    )


def e_link_documento(link):

    link_lower = link.lower()

    return any(
        estensione in link_lower
        for estensione in [
            ".pdf",
            ".doc",
            ".docx"
        ]
    )


def contiene_parola_esclusa(testo):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in PAROLE_DA_ESCLUDERE
    )


def e_documento_accessorio(
    titolo
):

    titolo_lower = titolo.lower()

    return any(
        parola in titolo_lower
        for parola in PAROLE_DOCUMENTO_ACCESSORIO
    )


def e_documento_principale(
    titolo,
    contesto,
    link
):

    titolo_lower = titolo.lower()

    contesto_lower = contesto.lower()

    link_lower = testo_link_decodificato(
        link
    ).lower()

    if e_documento_accessorio(
        titolo
    ):

        return False

    if any(
        parola in titolo_lower
        for parola in PAROLE_DOCUMENTO_PRINCIPALE
    ):

        return True

    if "bando" in link_lower:

        return True

    if (
        "decreto rettorale" in contesto_lower
        and (
            "procedura" in titolo_lower
            or "decreto" in titolo_lower
        )
    ):

        return True

    return False


def e_prima_fascia(testo):

    testo_lower = testo.lower()

    if contiene_parola_esclusa(
        testo
    ):

        return False

    ha_prima_fascia = any(
        parola in testo_lower
        for parola in PAROLE_PRIMA_FASCIA
    )

    ha_seconda_fascia = any(
        parola in testo_lower
        for parola in PAROLE_SECONDA_FASCIA
    )

    return (
        ha_prima_fascia
        and not ha_seconda_fascia
    )


def e_docenza_contratto(testo):

    testo_lower = testo.lower()

    if contiene_parola_esclusa(
        testo
    ):

        return False

    return any(
        parola in testo_lower
        for parola in PAROLE_DOCENZA_CONTRATTO
    )


def contiene_area_interesse(testo):

    testo_maiuscolo = testo.upper()

    for prefisso in PREFISSI_AREA_INTERESSE:

        if prefisso in testo_maiuscolo:

            return True

    parole_area = [
        "MEDICINA",
        "CHIRURGIA",
        "ODONTOIATRIA",
        "BIOLOGIA",
        "BIOMEDICINA",
        "FARMACOLOGIA",
        "ONCOLOGIA",
        "PATOLOGIA",
        "ANESTESIOLOGIA",
        "NEUROCHIRURGIA",
        "PEDIATRIA",
        "CARDIOLOGIA"
    ]

    return any(
        parola in testo_maiuscolo
        for parola in parole_area
    )


def estrai_codici_area(testo):

    testo_maiuscolo = unquote(
        testo
    ).upper()

    pattern = re.compile(
        r"\b(?:\d{2}/)?"
        r"(?:MEDS|MEDF|BIOS|MVET|IINF|PHYS|IBIO)"
        r"[- ]?\d{2}(?:[/ -]?[A-Z])?\b"
        r"|\b(?:BIO|MED|VET|FIS|ING-INF)"
        r"[/ -]?\d{2}\b"
    )

    codici = []

    for codice in pattern.findall(
        testo_maiuscolo
    ):

        codice = normalizza_testo(
            codice
        )

        if codice not in codici:

            codici.append(
                codice
            )

    return codici


def estrai_date_scadenza(testo):

    testo = normalizza_testo(
        testo
    )

    date_trovate = []

    pattern_numerico = re.compile(
        r"scadenza\s*:?\s*"
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        re.IGNORECASE
    )

    for giorno, mese, anno in pattern_numerico.findall(
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

    pattern_testuale = re.compile(
        r"scadenza\s*:?\s*"
        r"(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|"
        r"giugno|luglio|agosto|settembre|ottobre|"
        r"novembre|dicembre)\s+"
        r"(\d{4})",
        re.IGNORECASE
    )

    for giorno, mese_testo, anno in pattern_testuale.findall(
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


def scegli_scadenza(date_trovate):

    if not date_trovate:

        return (
            None,
            "Scadenza non individuata"
        )

    future = [
        data
        for data in date_trovate
        if data >= date.today()
    ]

    if future:

        data_scadenza = min(
            future
        )

    else:

        data_scadenza = max(
            date_trovate
        )

    return (
        data_scadenza,
        data_scadenza.strftime(
            "%d/%m/%Y"
        )
    )


def testo_vicino_link(
    elemento
):

    parti_precedenti = []

    parti_successive = []

    for vicino in elemento.previous_elements:

        if len(
            parti_precedenti
        ) >= 14:

            break

        if not isinstance(
            vicino,
            NavigableString
        ):

            continue

        testo = normalizza_testo(
            str(
                vicino
            )
        )

        if not testo:

            continue

        parti_precedenti.append(
            testo
        )

    for vicino in elemento.next_elements:

        if len(
            parti_successive
        ) >= 30:

            break

        if isinstance(
            vicino,
            Tag
        ):

            if (
                vicino.name == "a"
                and vicino is not elemento
                and vicino.get(
                    "href"
                )
            ):

                href = vicino.get(
                    "href",
                    ""
                )

                if e_link_documento(
                    href
                ):

                    break

            continue

        if not isinstance(
            vicino,
            NavigableString
        ):

            continue

        testo = normalizza_testo(
            str(
                vicino
            )
        )

        if not testo:

            continue

        parti_successive.append(
            testo
        )

    parti_precedenti.reverse()

    return normalizza_testo(
        " ".join(
            parti_precedenti
            + parti_successive
        )
    )


def contesto_documento(
    elemento
):

    contesto_vicino = testo_vicino_link(
        elemento
    )

    nodo = elemento.parent

    contesti_parent = []

    for _ in range(6):

        if nodo is None:

            break

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        if testo and len(
            testo
        ) <= 5000:

            contesti_parent.append(
                testo
            )

            if "scadenza" in testo.lower():

                break

        nodo = nodo.parent

    return normalizza_testo(
        contesto_vicino
        + " "
        + " ".join(
            contesti_parent
        )
    )


def scopri_pagine_docenza(
    sessione
):

    html = scarica_pagina(
        sessione,
        URL_INDICE_ROMA
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    pagine = {}

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        href = elemento.get(
            "href"
        )

        if not titolo or not href:

            continue

        titolo_lower = titolo.lower()

        if not any(
            parola in titolo_lower
            for parola in PAROLE_PAGINA_DOCENZA
        ):

            continue

        link = normalizza_link(
            href
        )

        if "progetti-ateneo-roma-" not in link.lower():

            continue

        pagine[
            link
        ] = {
            "nome": titolo,
            "tipo": "docenza",
            "url": link
        }

    print(
        "Pagine docenza Roma individuate:",
        len(pagine)
    )

    return list(
        pagine.values()
    )


def analizza_pagina(
    nome,
    tipo,
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

        if not href:

            continue

        link = normalizza_link(
            href
        )

        if link in links_visti:

            continue

        if not e_link_documento(
            link
        ):

            continue

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not titolo:

            continue

        contesto = contesto_documento(
            elemento
        )

        testo_completo = normalizza_testo(
            titolo
            + " "
            + contesto
            + " "
            + testo_link_decodificato(
                link
            )
        )

        if not e_documento_principale(
            titolo,
            contesto,
            link
        ):

            continue

        if tipo == "prima_fascia":

            if not e_prima_fascia(
                testo_completo
            ):

                continue

            if not contiene_area_interesse(
                testo_completo
            ):

                continue

        elif tipo == "docenza":

            if not e_docenza_contratto(
                testo_completo
            ):

                continue

        else:

            continue

        date_trovate = estrai_date_scadenza(
            testo_completo
        )

        data_scadenza, scadenza_testo = (
            scegli_scadenza(
                date_trovate
            )
        )

        codici_area = estrai_codici_area(
            testo_completo
        )

        links_visti.add(
            link
        )

        procedure.append(
            {
                "sezione": nome,
                "tipo": tipo,
                "titolo": titolo,
                "descrizione": contesto[:1200],
                "link": link,
                "codici_area": codici_area,
                "data_scadenza": data_scadenza,
                "scadenza_testo": scadenza_testo
            }
        )

    print(
        "Procedure pertinenti trovate:",
        len(procedure)
    )

    return procedure


def raccogli_procedure(
    sessione
):

    pagine_docenza = scopri_pagine_docenza(
        sessione
    )

    pagine = (
        PAGINE_PRIMA_FASCIA
        + pagine_docenza
    )

    tutte = []

    for pagina in pagine:

        print(
            "\nControllo sezione:",
            pagina["nome"]
        )

        try:

            html = scarica_pagina(
                sessione,
                pagina["url"]
            )

            procedure = analizza_pagina(
                pagina["nome"],
                pagina["tipo"],
                html
            )

            tutte.extend(
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

    return tutte


def procedura_aperta(
    procedura
):

    data_scadenza = procedura[
        "data_scadenza"
    ]

    if data_scadenza is None:

        print(
            "IGNORATA: scadenza non individuata:",
            procedura["link"]
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
        "Nuovi bandi Università Cattolica Roma",
        "",
        (
            "Nuove procedure ancora aperte "
            "corrispondenti ai criteri di interesse:"
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
            f"Tipologia: {bando['tipo']}"
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
            bando["descrizione"]
        )

        righe.append("")

        righe.append(
            "Documento principale:"
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
        "[CATTOLICA ROMA] Nuovi bandi"
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
    "\n=== MONITOR CATTOLICA ROMA ===\n"
)

sessione = crea_sessione()

storico = carica_storico()

gia_segnalati = set(
    storico.get(
        "bandi_gia_segnalati",
        []
    )
)

procedure = raccogli_procedure(
    sessione
)


procedure_uniche = {}

for procedura in procedure:

    procedure_uniche[
        procedura["link"]
    ] = procedura


procedure = list(
    procedure_uniche.values()
)


procedure_aperte = [
    procedura
    for procedura in procedure
    if procedura_aperta(
        procedura
    )
]


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
            "Sezione:",
            bando["sezione"]
        )

        print(
            "Tipologia:",
            bando["tipo"]
        )

        print(
            "Titolo:",
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
            "\nSTORICO CATTOLICA AGGIORNATO"
        )

    else:

        print(
            "Storico non aggiornato perché "
            "l'email non è stata inviata"
        )


print(
    "\n=== FINE MONITOR CATTOLICA ROMA ==="
)
