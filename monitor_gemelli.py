import json
import os
import re
import smtplib

from datetime import date, datetime
from email.mime.text import MIMEText
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


BASE_URL = (
    "https://policlinicogemelli.intervieweb.it"
)

URL_CARRIERE = (
    "https://policlinicogemelli.intervieweb.it/it/career"
)

FILE_STORICO = (
    "storico_gemelli.json"
)

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)


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


PAROLE_AREA_BIOMEDICA = [
    "biologo",
    "biologa",
    "biologi",
    "biologhe",
    "biologia",
    "biomedicina",
    "biomedico",
    "biomedica",
    "biomedici",
    "biomediche",
    "biotecnologo",
    "biotecnologa",
    "biotecnologi",
    "biotecnologie",
    "biochimica",
    "bioinformatica",
    "genetica",
    "genomica",
    "proteomica",
    "microbiologia",
    "immunologia",
    "farmacologia",
    "fisiologia",
    "patologia",
    "patologia generale",
    "patologia clinica",
    "laboratorio",
    "laboratorio biomedico",
    "laboratorio di ricerca",
    "ricerca biomedica",
    "ricerca clinica",
    "ricerca scientifica",
    "ricercatore",
    "ricercatrice",
    "clinical trial",
    "clinical research",
    "trial clinico",
    "trial clinici",
    "sperimentazione clinica",
    "studi clinici",
    "studio clinico",
    "epidemiologia",
    "biostatistica",
    "data scientist",
    "data science",
    "biobanca",
    "biobanking",
    "biomarcatori",
    "biomarkers",
    "malattie infettive",
    "hiv",
    "oncologia",
    "ematologia",
    "cardiologia",
    "neuroscienze",
    "neurobiologia",
    "neurochirurgia",
    "diagnostica",
    "diagnostica per immagini",
    "radiologia",
    "radioterapia",
    "medicina nucleare",
    "medico",
    "medica",
    "medici",
    "medicina",
    "chirurgia",
    "anestesia",
    "anestesiologia",
    "rianimazione",
    "pediatria",
    "nutrizione",
    "fisioterapia",
    "psicologia clinica",
    "infermiere",
    "infermiera",
    "infermieri",
    "infermieristica",
    "professioni sanitarie",
    "tecnico sanitario",
    "tecnica sanitaria",
    "tecnico di laboratorio",
    "tecnica di laboratorio",
    "tecnico di radiologia",
    "tecnica di radiologia",
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
    "ing-inf/"
]


PAROLE_RUOLO_AMMINISTRATIVO = [
    "segreteria",
    "assistente amministrativo",
    "assistente amministrativa",
    "addetto amministrativo",
    "addetta amministrativa",
    "amministrazione",
    "contabilità",
    "contabilita",
    "risorse umane",
    "ufficio acquisti",
    "reception",
    "centralino",
    "front office",
    "back office",
    "customer care",
    "ufficio legale",
    "marketing",
    "comunicazione",
    "fundraising"
]


PAROLE_TEMPO_INDETERMINATO = [
    "tempo indeterminato",
    "contratto a tempo indeterminato",
    "assunzione a tempo indeterminato",
    "contratto di lavoro a tempo indeterminato",
    "rapporto di lavoro a tempo indeterminato",
    "permanent contract",
    "permanent position",
    "permanent employment"
]


PAROLE_TEMPO_DETERMINATO = [
    "tempo determinato",
    "contratto a tempo determinato",
    "contratto di lavoro a tempo determinato",
    "rapporto di lavoro a tempo determinato",
    "fixed-term contract",
    "fixed term contract"
]


PAROLE_COCOCO = [
    "collaborazione coordinata e continuativa",
    "co.co.co",
    "co.co.co.",
    "cococo"
]


PAROLE_LIBERO_PROFESSIONALE = [
    "libero professionale",
    "libera professione",
    "contratto libero professionale",
    "contratto di libera professione",
    "partita iva"
]


PAROLE_BORSA = [
    "borsa di studio",
    "borse di studio",
    "borsista"
]


PAROLE_STAGE = [
    "stage",
    "tirocinio",
    "internship"
]


PAROLE_ALTRI_CONTRATTI = [
    "apprendistato",
    "somministrazione",
    "contratto occasionale",
    "collaborazione occasionale",
    "servizio civile"
]


PAROLE_DA_ESCLUDERE = [
    "candidatura spontanea",
    "login",
    "recupero password",
    "privacy",
    "cookie",
    "informativa"
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

        offerte = storico.get(
            "offerte_gia_segnalate"
        )

        if not isinstance(
            offerte,
            list
        ):

            storico[
                "offerte_gia_segnalate"
            ] = []

        return storico

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ):

        return {
            "offerte_gia_segnalate": []
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


def contiene_parola(
    testo,
    parole
):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in parole
    )


def contiene_docenza(testo):

    return contiene_parola(
        testo,
        PAROLE_DOCENZA_CONTRATTO
    )


def contiene_area_biomedica(testo):

    return contiene_parola(
        testo,
        PAROLE_AREA_BIOMEDICA
    )


def titolo_amministrativo(titolo):

    return contiene_parola(
        titolo,
        PAROLE_RUOLO_AMMINISTRATIVO
    )


def e_offerta_pertinente(
    titolo,
    testo_completo
):

    docenza = contiene_docenza(
        testo_completo
    )

    area_biomedica = contiene_area_biomedica(
        testo_completo
    )

    if docenza:

        return True

    if titolo_amministrativo(
        titolo
    ):

        return False

    return area_biomedica


def classifica_contratto(testo):

    testo_lower = testo.lower()

    if any(
        parola in testo_lower
        for parola in PAROLE_TEMPO_INDETERMINATO
    ):

        return "Tempo indeterminato"

    if any(
        parola in testo_lower
        for parola in PAROLE_TEMPO_DETERMINATO
    ):

        return "Tempo determinato"

    if any(
        parola in testo_lower
        for parola in PAROLE_COCOCO
    ):

        return "Collaborazione coordinata e continuativa"

    if any(
        parola in testo_lower
        for parola in PAROLE_LIBERO_PROFESSIONALE
    ):

        return "Contratto libero-professionale"

    if any(
        parola in testo_lower
        for parola in PAROLE_BORSA
    ):

        return "Borsa di studio"

    if any(
        parola in testo_lower
        for parola in PAROLE_STAGE
    ):

        return "Stage o tirocinio"

    if any(
        parola in testo_lower
        for parola in PAROLE_ALTRI_CONTRATTI
    ):

        return "Altra forma contrattuale"

    return "Contratto non specificato"


def estrai_scadenza(testo):

    pattern = re.compile(
        r"scadenza"
        r"(?:\s+presentazione\s+domanda)?"
        r"\s*:?\s*"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    corrispondenze = pattern.findall(
        testo
    )

    date_valide = []

    for data_testo in corrispondenze:

        try:

            data_scadenza = datetime.strptime(
                data_testo,
                "%d/%m/%Y"
            ).date()

            if data_scadenza not in date_valide:

                date_valide.append(
                    data_scadenza
                )

        except ValueError:

            continue

    if not date_valide:

        return (
            None,
            "Scadenza non specificata"
        )

    date_future = [
        data_scadenza
        for data_scadenza in date_valide
        if data_scadenza >= date.today()
    ]

    if date_future:

        data_scadenza = min(
            date_future
        )

    else:

        data_scadenza = max(
            date_valide
        )

    return (
        data_scadenza,
        data_scadenza.strftime(
            "%d/%m/%Y"
        )
    )


def estrai_data_pubblicazione(testo):

    pattern = re.compile(
        r"data\s+di\s+pubblicazione"
        r"\s*:?\s*"
        r"(\d{1,2}/\d{1,2}/\d{4})",
        re.IGNORECASE
    )

    corrispondenza = pattern.search(
        testo
    )

    if not corrispondenza:

        return "Data di pubblicazione non specificata"

    return corrispondenza.group(
        1
    )


def estrai_annunci(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    annunci = {}

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

        if "/jobs/" not in link.lower():

            continue

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not titolo:

            continue

        if contiene_parola(
            titolo + " " + link,
            PAROLE_DA_ESCLUDERE
        ):

            continue

        if (
            link not in annunci
            or len(titolo) > len(
                annunci[link]["titolo"]
            )
        ):

            annunci[
                link
            ] = {
                "titolo": titolo,
                "link": link
            }

    return list(
        annunci.values()
    )


def trova_url_ajax(
    soup
):

    elemento = soup.find(
        id="url-for-announces"
    )

    if elemento is None:

        return None

    valore = elemento.get(
        "value"
    )

    if not valore:

        return None

    return normalizza_link(
        valore
    )


def trova_section_ajax(html):

    pattern = re.compile(
        r"""[^'"]+['"]""",
        re.IGNORECASE
    )

    corrispondenza = pattern.search(
        html
    )

    if not corrispondenza:

        print(
            "Parametro section AJAX non individuato"
        )

        return None

    valore_section = corrispondenza.group(
        1
    )

    print(
        "Parametro section AJAX:",
        valore_section
    )

    return valore_section


def scarica_pagine_ajax(
    sessione,
    html_principale
):

    soup = BeautifulSoup(
        html_principale,
        "html.parser"
    )

    url_ajax = trova_url_ajax(
        soup
    )

    section = trova_section_ajax(
        html_principale
    )

    if not url_ajax:

        print(
            "URL AJAX non individuato, "
            "uso soltanto la pagina principale"
        )

        return []

    if not section:

        print(
            "Parametro section non individuato, "
            "uso soltanto la pagina principale"
        )

        return []

    annunci_extra = []

    links_precedenti = set()

    for pagina in range(
        2,
        11
    ):

        dati = {
            "act1": "vacancyListCareer",
            "section": section,
            "order": "",
            "page": pagina,
            "country": "",
            "region": "",
            "function": "",
            "project": "",
            "text": "",
            "division": "",
            "company": ""
        }

        try:

            risposta = sessione.post(
                url_ajax,
                data=dati,
                timeout=60
            )

            risposta.raise_for_status()

        except Exception as errore:

            print(
                "Errore durante il caricamento "
                f"della pagina AJAX {pagina}:"
            )

            print(
                str(
                    errore
                )
            )

            break

        annunci_pagina = estrai_annunci(
            risposta.text
        )

        links_pagina = {
            annuncio["link"]
            for annuncio in annunci_pagina
        }

        links_nuovi = (
            links_pagina
            - links_precedenti
        )

        print(
            f"Pagina AJAX {pagina}:",
            len(annunci_pagina),
            "annunci"
        )

        if not annunci_pagina:

            break

        if not links_nuovi:

            break

        annunci_extra.extend(
            annunci_pagina
        )

        links_precedenti.update(
            links_pagina
        )

    return annunci_extra


def estrai_descrizione(
    soup,
    testo_completo
):

    selettori = [
        ".vacancy-description",
        ".job-description",
        ".description",
        ".announce-description",
        "[itemprop='description']"
    ]

    for selettore in selettori:

        elemento = soup.select_one(
            selettore
        )

        if elemento is None:

            continue

        testo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if testo:

            return testo[:1800]

    return testo_completo[:1800]


def analizza_dettaglio(
    sessione,
    annuncio
):

    try:

        html = scarica_pagina(
            sessione,
            annuncio["link"]
        )

    except Exception as errore:

        print(
            "ERRORE NEL DETTAGLIO:",
            annuncio["link"]
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

    titolo = annuncio[
        "titolo"
    ]

    intestazioni = soup.find_all(
        ["h1", "h2"]
    )

    for intestazione in intestazioni:

        titolo_intestazione = normalizza_testo(
            intestazione.get_text(
                " ",
                strip=True
            )
        )

        if not titolo_intestazione:

            continue

        if (
            "fondazione policlinico" in
            titolo_intestazione.lower()
        ):

            continue

        if len(
            titolo_intestazione
        ) > len(
            titolo
        ):

            titolo = titolo_intestazione

    testo_completo = normalizza_testo(
        titolo
        + " "
        + testo
        + " "
        + annuncio["link"]
    )

    if not e_offerta_pertinente(
        titolo,
        testo_completo
    ):

        return None

    data_scadenza, scadenza_testo = (
        estrai_scadenza(
            testo_completo
        )
    )

    return {
        "titolo": titolo,
        "link": annuncio["link"],
        "area_biomedica": contiene_area_biomedica(
            testo_completo
        ),
        "docenza": contiene_docenza(
            testo_completo
        ),
        "contratto": classifica_contratto(
            testo_completo
        ),
        "data_pubblicazione": estrai_data_pubblicazione(
            testo_completo
        ),
        "data_scadenza": data_scadenza,
        "scadenza_testo": scadenza_testo,
        "descrizione": estrai_descrizione(
            soup,
            testo
        )
    }


def offerta_attiva(
    offerta
):

    data_scadenza = offerta[
        "data_scadenza"
    ]

    if data_scadenza is None:

        return True

    return data_scadenza >= date.today()


def invia_email(
    offerte_nuove
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
        "Nuove opportunità Gemelli IRCCS",
        "",
        (
            "Sono state individuate nuove opportunità "
            "biomediche, scientifiche, sanitarie "
            "o didattiche."
        ),
        "",
        (
            "La tipologia contrattuale è riportata "
            "come informazione e non costituisce "
            "un criterio di esclusione."
        ),
        ""
    ]

    for numero, offerta in enumerate(
        offerte_nuove,
        start=1
    ):

        righe.append(
            "========================================"
        )

        righe.append(
            f"OFFERTA {numero}"
        )

        righe.append(
            "========================================"
        )

        righe.append(
            f"Contratto: {offerta['contratto']}"
        )

        righe.append(
            "Pubblicazione: "
            + offerta["data_pubblicazione"]
        )

        righe.append(
            f"Scadenza: {offerta['scadenza_testo']}"
        )

        righe.append(
            "Area biomedica/scientifica: "
            + (
                "Sì"
                if offerta["area_biomedica"]
                else "No"
            )
        )

        righe.append(
            "Docenza/insegnamento: "
            + (
                "Sì"
                if offerta["docenza"]
                else "No"
            )
        )

        righe.append("")

        righe.append(
            offerta["titolo"]
        )

        righe.append("")

        righe.append(
            offerta["descrizione"]
        )

        righe.append("")

        righe.append(
            "Link all'offerta:"
        )

        righe.append(
            offerta["link"]
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
        "[GEMELLI IRCCS] Nuove opportunità"
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
    "\n=== MONITOR GEMELLI IRCCS ===\n"
)

sessione = crea_sessione()

storico = carica_storico()

gia_segnalate = set(
    storico.get(
        "offerte_gia_segnalate",
        []
    )
)

html_principale = scarica_pagina(
    sessione,
    URL_CARRIERE
)

annunci = estrai_annunci(
    html_principale
)

annunci_extra = scarica_pagine_ajax(
    sessione,
    html_principale
)

annunci_unici = {}

for annuncio in (
    annunci
    + annunci_extra
):

    annunci_unici[
        annuncio["link"]
    ] = annuncio


annunci = list(
    annunci_unici.values()
)


print(
    "\nAnnunci complessivi individuati:",
    len(annunci)
)


offerte_pertinenti = []

for annuncio in annunci:

    dettaglio = analizza_dettaglio(
        sessione,
        annuncio
    )

    if dettaglio is None:

        continue

    offerte_pertinenti.append(
        dettaglio
    )


offerte_uniche = {}

for offerta in offerte_pertinenti:

    offerte_uniche[
        offerta["link"]
    ] = offerta


offerte_pertinenti = list(
    offerte_uniche.values()
)


offerte_attive = [
    offerta
    for offerta in offerte_pertinenti
    if offerta_attiva(
        offerta
    )
]


offerte_nuove = [
    offerta
    for offerta in offerte_attive
    if offerta["link"] not in gia_segnalate
]


print(
    "Offerte pertinenti:",
    len(offerte_pertinenti)
)

print(
    "Offerte attive:",
    len(offerte_attive)
)

print(
    "Nuove offerte da segnalare:",
    len(offerte_nuove)
)


if not offerte_nuove:

    print(
        "NESSUNA NUOVA OFFERTA"
    )

else:

    for offerta in offerte_nuove:

        print(
            "\nNUOVA OFFERTA:"
        )

        print(
            "Titolo:",
            offerta["titolo"]
        )

        print(
            "Contratto:",
            offerta["contratto"]
        )

        print(
            "Pubblicazione:",
            offerta["data_pubblicazione"]
        )

        print(
            "Scadenza:",
            offerta["scadenza_testo"]
        )

        print(
            "Area biomedica:",
            offerta["area_biomedica"]
        )

        print(
            "Docenza:",
            offerta["docenza"]
        )

        print(
            "Link:",
            offerta["link"]
        )

    email_inviata = invia_email(
        offerte_nuove
    )

    if email_inviata:

        for offerta in offerte_nuove:

            storico[
                "offerte_gia_segnalate"
            ].append(
                offerta["link"]
            )

        salva_storico(
            storico
        )

        print(
            "\nSTORICO GEMELLI AGGIORNATO"
        )

    else:

        print(
            "Storico non aggiornato perché "
            "l'email non è stata inviata"
        )


print(
    "\n=== FINE MONITOR GEMELLI IRCCS ==="
)
