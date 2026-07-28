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


BASE_URL = "https://policlinicogemelli.intervieweb.it"

URL_CARRIERE = (
    "https://policlinicogemelli.intervieweb.it/it/career"
)

FILE_STORICO = "storico_gemelli.json"

EMAIL_ADDRESS = os.getenv(
    "EMAIL_ADDRESS"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)


# =========================================================
# PAROLE CHIAVE PER L'AREA DI INTERESSE
# =========================================================

PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "professore a contratto",
    "professori a contratto",
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
    "attività didattica"
]


PAROLE_BIOMEDICHE = [
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
    "laboratorio biomedico",
    "laboratorio di ricerca",
    "ricerca biomedica",
    "ricerca clinica",
    "ricerca scientifica",
    "ricercatore biomedico",
    "ricercatrice biomedica",
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
    "healthcare",
    "value based healthcare",
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


# Queste parole nel titolo identificano ruoli non coerenti
# con il monitor, anche se il reparto è medico o scientifico.

PAROLE_RUOLI_DA_ESCLUDERE = [
    "addetto alla segreteria",
    "addetta alla segreteria",
    "addetto/a alla segreteria",
    "assistente amministrativo",
    "assistente amministrativa",
    "assistente amministrativo/a",
    "addetto amministrativo",
    "addetta amministrativa",
    "addetto/a amministrativo",
    "data entry",
    "revisore esterno",
    "revisori esterni",
    "contabilita",
    "contabilità",
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


PAROLE_DA_ESCLUDERE_SEMPRE = [
    "candidatura spontanea",
    "recupero password",
    "carica il cv per registrarti",
    "non hai ancora un profilo"
]


# =========================================================
# CLASSIFICAZIONE DEL CONTRATTO
# =========================================================

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


# =========================================================
# STORICO
# =========================================================

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


# =========================================================
# CONNESSIONE
# =========================================================

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


# =========================================================
# FUNZIONI GENERALI
# =========================================================

def normalizza_testo(testo):

    if testo is None:

        return ""

    return " ".join(
        unescape(
            str(
                testo
            )
        ).split()
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


def titolo_da_escludere(titolo):

    return contiene_parola(
        titolo,
        PAROLE_RUOLI_DA_ESCLUDERE
    )


def contiene_docenza(testo):

    return contiene_parola(
        testo,
        PAROLE_DOCENZA
    )


def contiene_area_biomedica(testo):

    return contiene_parola(
        testo,
        PAROLE_BIOMEDICHE
    )


def e_offerta_pertinente(
    titolo,
    descrizione
):

    titolo = normalizza_testo(
        titolo
    )

    descrizione = normalizza_testo(
        descrizione
    )

    if contiene_parola(
        titolo,
        PAROLE_DA_ESCLUDERE_SEMPRE
    ):

        return False

    if titolo_da_escludere(
        titolo
    ):

        return False

    # La docenza deve essere presente nel titolo oppure
    # nella descrizione specifica dell'offerta.

    if contiene_docenza(
        titolo
    ):

        return True

    if contiene_docenza(
        descrizione
    ):

        return True

    # La pertinenza biomedicale viene valutata prima
    # sul titolo, che è la fonte più affidabile.

    if contiene_area_biomedica(
        titolo
    ):

        return True

    # Per titoli generici come "Bando PNRR", viene usata
    # anche la descrizione specifica dell'offerta.

    titoli_generici = [
        "bando",
        "avviso",
        "specialista",
        "ricercatore",
        "ricercatrice"
    ]

    titolo_lower = titolo.lower()

    if any(
        parola in titolo_lower
        for parola in titoli_generici
    ):

        return contiene_area_biomedica(
            descrizione
        )

    return False


# =========================================================
# CONTRATTO
# =========================================================

def classifica_contratto(
    titolo,
    descrizione
):

    testo = normalizza_testo(
        titolo
        + " "
        + descrizione
    ).lower()

    if any(
        parola in testo
        for parola in PAROLE_TEMPO_INDETERMINATO
    ):

        return "Tempo indeterminato"

    if any(
        parola in testo
        for parola in PAROLE_TEMPO_DETERMINATO
    ):

        return "Tempo determinato"

    if any(
        parola in testo
        for parola in PAROLE_COCOCO
    ):

        return (
            "Collaborazione coordinata "
            "e continuativa"
        )

    if any(
        parola in testo
        for parola in PAROLE_LIBERO_PROFESSIONALE
    ):

        return "Contratto libero-professionale"

    if any(
        parola in testo
        for parola in PAROLE_BORSA
    ):

        return "Borsa di studio"

    if any(
        parola in testo
        for parola in PAROLE_STAGE
    ):

        return "Stage o tirocinio"

    if any(
        parola in testo
        for parola in PAROLE_ALTRI_CONTRATTI
    ):

        return "Altra forma contrattuale"

    return "Contratto non specificato"


# =========================================================
# DATE
# =========================================================

def converti_data(data_testo):

    if not data_testo:

        return None

    data_testo = data_testo.strip()

    data_testo = data_testo.replace(
        "Z",
        "+00:00"
    )

    formati = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for formato in formati:

        try:

            return datetime.strptime(
                data_testo,
                formato
            ).date()

        except ValueError:

            continue

    try:

        return datetime.fromisoformat(
            data_testo
        ).date()

    except ValueError:

        return None


def estrai_scadenza_da_testo(testo):

    patterns = [
        re.compile(
            r"scadenza"
            r"(?:\s+presentazione\s+domanda)?"
            r"\s*:?\s*"
            r"(\d{1,2}/\d{1,2}/\d{4})",
            re.IGNORECASE
        ),
        re.compile(
            r"termine"
            r"(?:\s+per\s+la)?"
            r"(?:\s+presentazione\s+(?:della\s+)?domanda)?"
            r"\s*:?\s*"
            r"(\d{1,2}/\d{1,2}/\d{4})",
            re.IGNORECASE
        )
    ]

    date_trovate = []

    for pattern in patterns:

        for data_testo in pattern.findall(
            testo
        ):

            data_scadenza = converti_data(
                data_testo
            )

            if (
                data_scadenza is not None
                and data_scadenza not in date_trovate
            ):

                date_trovate.append(
                    data_scadenza
                )

    if not date_trovate:

        return None

    date_future = [
        data_scadenza
        for data_scadenza in date_trovate
        if data_scadenza >= date.today()
    ]

    if date_future:

        return min(
            date_future
        )

    return max(
        date_trovate
    )


def estrai_pubblicazione_da_testo(testo):

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

        return None

    return converti_data(
        corrispondenza.group(
            1
        )
    )


def formatta_data(
    data_valore,
    testo_default
):

    if data_valore is None:

        return testo_default

    return data_valore.strftime(
        "%d/%m/%Y"
    )


# =========================================================
# JSON-LD DELLA SINGOLA OFFERTA
# =========================================================

def raccogli_oggetti_json(
    valore
):

    risultati = []

    if isinstance(
        valore,
        dict
    ):

        risultati.append(
            valore
        )

        for sotto_valore in valore.values():

            risultati.extend(
                raccogli_oggetti_json(
                    sotto_valore
                )
            )

    elif isinstance(
        valore,
        list
    ):

        for elemento in valore:

            risultati.extend(
                raccogli_oggetti_json(
                    elemento
                )
            )

    return risultati


def estrai_jobposting_jsonld(soup):

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        contenuto = script.string

        if not contenuto:

            continue

        try:

            dati = json.loads(
                contenuto
            )

        except json.JSONDecodeError:

            continue

        for oggetto in raccogli_oggetti_json(
            dati
        ):

            tipo = oggetto.get(
                "@type"
            )

            if isinstance(
                tipo,
                list
            ):

                tipi = [
                    str(
                        elemento
                    ).lower()
                    for elemento in tipo
                ]

            else:

                tipi = [
                    str(
                        tipo
                    ).lower()
                ]

            if "jobposting" in tipi:

                return oggetto

    return None


def pulisci_html_testo(testo_html):

    if not testo_html:

        return ""

    soup = BeautifulSoup(
        str(
            testo_html
        ),
        "html.parser"
    )

    return normalizza_testo(
        soup.get_text(
            " ",
            strip=True
        )
    )


# =========================================================
# ESTRAZIONE DALL'ELENCO
# =========================================================

def estrai_annunci(html):

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
            titolo,
            PAROLE_DA_ESCLUDERE_SEMPRE
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


# =========================================================
# CONTENUTO SPECIFICO DEL DETTAGLIO
# =========================================================

def rimuovi_elementi_comuni(soup):

    for selettore in [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "form",
        "aside",
        ".login",
        ".register",
        ".registration",
        ".candidate-registration",
        ".privacy",
        ".cookie",
        ".modal"
    ]:

        for elemento in soup.select(
            selettore
        ):

            elemento.decompose()


def estrai_contenuto_specifico(soup):

    selettori = [
        "[itemprop='description']",
        ".vacancy-description",
        ".job-description",
        ".announce-description",
        ".description",
        ".vacancy-detail",
        ".job-detail",
        "article",
        "main",
        "#contenutipagine"
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

        if len(testo) >= 100:

            return testo

    return ""


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

    soup_originale = BeautifulSoup(
        html,
        "html.parser"
    )

    jobposting = estrai_jobposting_jsonld(
        soup_originale
    )

    # Il titolo affidabile resta sempre quello
    # già estratto dalla lista degli annunci.

    titolo = annuncio[
        "titolo"
    ]

    descrizione = ""

    data_pubblicazione = None

    data_scadenza = None

    contratto_schema = ""

    if jobposting is not None:

        descrizione = pulisci_html_testo(
            jobposting.get(
                "description",
                ""
            )
        )

        data_pubblicazione = converti_data(
            str(
                jobposting.get(
                    "datePosted",
                    ""
                )
            )
        )

        data_scadenza = converti_data(
            str(
                jobposting.get(
                    "validThrough",
                    ""
                )
            )
        )

        contratto_schema = normalizza_testo(
            jobposting.get(
                "employmentType",
                ""
            )
        )

    if not descrizione:

        soup_specifico = BeautifulSoup(
            html,
            "html.parser"
        )

        rimuovi_elementi_comuni(
            soup_specifico
        )

        descrizione = estrai_contenuto_specifico(
            soup_specifico
        )

    if not descrizione:

        print(
            "IGNORATA: contenuto specifico "
            "dell'offerta non individuato:",
            annuncio["link"]
        )

        return None

    # Le date vengono cercate esclusivamente nella
    # descrizione specifica, non nell'intera pagina.

    if data_scadenza is None:

        data_scadenza = estrai_scadenza_da_testo(
            descrizione
        )

    if data_pubblicazione is None:

        data_pubblicazione = estrai_pubblicazione_da_testo(
            descrizione
        )

    if not e_offerta_pertinente(
        titolo,
        descrizione
    ):

        print(
            "ESCLUSA per scarsa pertinenza:",
            titolo
        )

        return None

    testo_contratto = normalizza_testo(
        titolo
        + " "
        + descrizione
        + " "
        + contratto_schema
    )

    return {
        "titolo": titolo,
        "link": annuncio["link"],
        "descrizione": descrizione[:1800],
        "area_biomedica": contiene_area_biomedica(
            titolo
            + " "
            + descrizione
        ),
        "docenza": contiene_docenza(
            titolo
            + " "
            + descrizione
        ),
        "contratto": classifica_contratto(
            titolo,
            testo_contratto
        ),
        "data_pubblicazione": data_pubblicazione,
        "data_scadenza": data_scadenza,
        "pubblicazione_testo": formatta_data(
            data_pubblicazione,
            "Data di pubblicazione non specificata"
        ),
        "scadenza_testo": formatta_data(
            data_scadenza,
            "Scadenza non specificata"
        )
    }


def offerta_attiva(offerta):

    data_scadenza = offerta[
        "data_scadenza"
    ]

    # Se non è indicata una scadenza, l'offerta è
    # considerata attiva finché compare nell'elenco.

    if data_scadenza is None:

        return True

    return data_scadenza >= date.today()


# =========================================================
# EMAIL
# =========================================================

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
            + offerta["pubblicazione_testo"]
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


# =========================================================
# MAIN
# =========================================================

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


print(
    "\nAnnunci complessivi individuati:",
    len(annunci)
)


offerte_pertinenti = []

for annuncio in annunci:

    # Prima esclusione basata sul vero titolo
    # estratto dall'elenco.

    if titolo_da_escludere(
        annuncio["titolo"]
    ):

        print(
            "ESCLUSA per ruolo amministrativo/operativo:",
            annuncio["titolo"]
        )

        continue

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
    "\nOfferte pertinenti:",
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
            offerta["pubblicazione_testo"]
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
