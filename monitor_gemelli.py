import re
import requests

from datetime import date, datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup


BASE_URL = (
    "https://policlinicogemelli.intervieweb.it"
)

URL_CARRIERE = (
    "https://policlinicogemelli.intervieweb.it/it/career"
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
    "biologia",
    "biomedicina",
    "biomedico",
    "biomedica",
    "biotecnologie",
    "ricerca",
    "ricercatore",
    "ricercatrice",
    "laboratorio",
    "medico",
    "medica",
    "medicina",
    "chirurgia",
    "neurochirurgia",
    "oncologia",
    "ematologia",
    "cardiologia",
    "microbiologia",
    "immunologia",
    "farmacologia",
    "patologia",
    "genetica",
    "genomica",
    "bioinformatica",
    "data scientist",
    "clinical trial",
    "sperimentazione clinica",
    "epidemiologia",
    "malattie infettive",
    "diagnostica",
    "radiologia",
    "fisiologia",
    "nutrizione",
    "psicologia",
    "neuroscienze",
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


PAROLE_CONTRATTO_TEMPORANEO = [
    "tempo determinato",
    "contratto a tempo determinato",
    "collaborazione coordinata e continuativa",
    "co.co.co",
    "co.co.co.",
    "cococo",
    "libero professionale",
    "libera professione",
    "partita iva",
    "borsa di studio",
    "borsista",
    "stage",
    "tirocinio",
    "servizio civile",
    "contratto di collaborazione",
    "contratto occasionale",
    "somministrazione",
    "apprendistato"
]


PAROLE_DA_ESCLUDERE = [
    "candidatura spontanea",
    "login",
    "recupero password",
    "privacy",
    "cookie",
    "informativa"
]


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

    print(
        "Status code:",
        risposta.status_code
    )

    print(
        "Pagina letta:",
        risposta.url
    )

    risposta.raise_for_status()

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


def contiene_area_biomedica(testo):

    return contiene_parola(
        testo,
        PAROLE_AREA_BIOMEDICA
    )


def contiene_docenza(testo):

    return contiene_parola(
        testo,
        PAROLE_DOCENZA_CONTRATTO
    )


def classifica_contratto(testo):

    testo_lower = testo.lower()

    if any(
        parola in testo_lower
        for parola in PAROLE_TEMPO_INDETERMINATO
    ):

        return "TEMPO INDETERMINATO"

    if any(
        parola in testo_lower
        for parola in PAROLE_CONTRATTO_TEMPORANEO
    ):

        return "CONTRATTO TEMPORANEO O NON PRIORITARIO"

    return "CONTRATTO NON SPECIFICATO"


def estrai_scadenza(testo):

    pattern = re.compile(
        r"scadenza(?:\s+presentazione\s+domanda)?"
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

            date_valide.append(
                data_scadenza
            )

        except ValueError:

            continue

    if not date_valide:

        return (
            None,
            "Scadenza non individuata"
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

        if link not in annunci:

            annunci[
                link
            ] = {
                "titolo": titolo,
                "link": link
            }

        elif len(titolo) > len(
            annunci[link]["titolo"]
        ):

            annunci[
                link
            ]["titolo"] = titolo

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


def estrai_pagine_html(
    soup
):

    links = []

    for elemento in soup.find_all(
        "a",
        href=True
    ):

        href = elemento.get(
            "href"
        )

        testo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        if not href:

            continue

        link = normalizza_link(
            href
        )

        testo_completo = (
            testo
            + " "
            + link
        ).lower()

        if (
            "page=2" in testo_completo
            or "pagina 2" in testo_completo
        ):

            if link not in links:

                links.append(
                    link
                )

    return links


def prova_pagina_due(
    sessione,
    soup
):

    urls = estrai_pagine_html(
        soup
    )

    urls_candidate = [
        URL_CARRIERE + "?page=2",
        URL_CARRIERE + "?p=2",
        URL_CARRIERE + "/2"
    ]

    for url in urls_candidate:

        if url not in urls:

            urls.append(
                url
            )

    annunci_pagina_due = []

    for url in urls:

        try:

            risposta = sessione.get(
                url,
                timeout=60
            )

            if risposta.status_code != 200:

                continue

            annunci = estrai_annunci(
                risposta.text
            )

            if annunci:

                print(
                    "Possibile pagina aggiuntiva:",
                    risposta.url
                )

                print(
                    "Annunci trovati:",
                    len(annunci)
                )

                annunci_pagina_due.extend(
                    annunci
                )

        except Exception as errore:

            print(
                "Errore tentativo pagina aggiuntiva:",
                url
            )

            print(
                str(
                    errore
                )
            )

    return annunci_pagina_due


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

    area_biomedica = contiene_area_biomedica(
        testo_completo
    )

    docenza = contiene_docenza(
        testo_completo
    )

    contratto = classifica_contratto(
        testo_completo
    )

    data_scadenza, scadenza_testo = (
        estrai_scadenza(
            testo_completo
        )
    )

    return {
        "titolo": titolo,
        "link": annuncio["link"],
        "area_biomedica": area_biomedica,
        "docenza": docenza,
        "contratto": contratto,
        "data_scadenza": data_scadenza,
        "scadenza_testo": scadenza_testo,
        "testo": testo
    }


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== DIAGNOSTICA DETTAGLI GEMELLI IRCCS ===\n"
)

sessione = crea_sessione()

html = scarica_pagina(
    sessione,
    URL_CARRIERE
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

url_ajax = trova_url_ajax(
    soup
)

print(
    "\nURL AJAX ANNUNCI:",
    url_ajax
)

annunci = estrai_annunci(
    html
)

annunci_extra = prova_pagina_due(
    sessione,
    soup
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
    "\nANNUNCI UNICI DA ANALIZZARE:",
    len(annunci)
)


dettagli_interessanti = []

for annuncio in annunci:

    testo_preliminare = (
        annuncio["titolo"]
        + " "
        + annuncio["link"]
    )

    if not (
        contiene_area_biomedica(
            testo_preliminare
        )
        or contiene_docenza(
            testo_preliminare
        )
    ):

        continue

    dettaglio = analizza_dettaglio(
        sessione,
        annuncio
    )

    if dettaglio is None:

        continue

    if not (
        dettaglio["area_biomedica"]
        or dettaglio["docenza"]
    ):

        continue

    dettagli_interessanti.append(
        dettaglio
    )


print(
    "\nDETTAGLI BIOMEDICI O DI DOCENZA:",
    len(dettagli_interessanti)
)


for numero, dettaglio in enumerate(
    dettagli_interessanti,
    start=1
):

    print(
        "\n========================================"
    )

    print(
        "OFFERTA:",
        numero
    )

    print(
        "========================================"
    )

    print(
        "TITOLO:",
        dettaglio["titolo"]
    )

    print(
        "AREA BIOMEDICA:",
        dettaglio["area_biomedica"]
    )

    print(
        "DOCENZA/INSEGNAMENTO:",
        dettaglio["docenza"]
    )

    print(
        "CONTRATTO:",
        dettaglio["contratto"]
    )

    print(
        "SCADENZA:",
        dettaglio["scadenza_testo"]
    )

    print(
        "LINK:",
        dettaglio["link"]
    )

    print(
        "TESTO DETTAGLIO:",
        dettaglio["testo"][:2500]
    )


print(
    "\n=== FINE DIAGNOSTICA DETTAGLI GEMELLI IRCCS ==="
)
