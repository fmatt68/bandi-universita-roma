import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit


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
    "indeterminato",
    "permanent contract",
    "permanent position"
]


PAROLE_CONTRATTI_NON_PRIORITARI = [
    "tempo determinato",
    "contratto a tempo determinato",
    "collaborazione coordinata e continuativa",
    "co.co.co",
    "cococo",
    "libero professionale",
    "partita iva",
    "borsa di studio",
    "stage",
    "tirocinio",
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
        "URL finale:",
        risposta.url
    )

    print(
        "Dimensione HTML:",
        len(risposta.text)
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


def contiene_tempo_indeterminato(testo):

    return contiene_parola(
        testo,
        PAROLE_TEMPO_INDETERMINATO
    )


def contiene_contratto_non_prioritario(testo):

    return contiene_parola(
        testo,
        PAROLE_CONTRATTI_NON_PRIORITARI
    )


def link_da_escludere(
    titolo,
    link
):

    testo = (
        titolo
        + " "
        + link
    )

    return contiene_parola(
        testo,
        PAROLE_DA_ESCLUDERE
    )


def sembra_link_offerta(
    titolo,
    link
):

    testo = (
        titolo
        + " "
        + link
    ).lower()

    indicatori_link = [
        "/career/",
        "/job/",
        "/jobs/",
        "/annuncio/",
        "/vacancy/",
        "/position/",
        "/offerta/",
        "detail",
        "apply"
    ]

    if any(
        indicatore in testo
        for indicatore in indicatori_link
    ):

        return True

    indicatori_titolo = [
        "bando",
        "medico",
        "medica",
        "biologo",
        "biologa",
        "ricerca",
        "ricercatore",
        "ricercatrice",
        "specialista",
        "data scientist",
        "clinical trial",
        "laboratorio",
        "docente",
        "professore",
        "insegnamento"
    ]

    return any(
        indicatore in titolo.lower()
        for indicatore in indicatori_titolo
    )


def trova_contenitore_offerta(
    elemento
):

    nodo = elemento

    miglior_nodo = elemento.parent

    for _ in range(8):

        if nodo is None:

            break

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        if (
            testo
            and len(testo) <= 6000
        ):

            miglior_nodo = nodo

        testo_lower = testo.lower()

        contiene_dati_offerta = any(
            parola in testo_lower
            for parola in [
                "data di pubblicazione",
                "scadenza",
                "invia candidatura",
                "roma italia",
                "chi stiamo cercando",
                "codice rif",
                "professione/funzione"
            ]
        )

        if (
            contiene_dati_offerta
            and len(testo) <= 6000
        ):

            return nodo

        nodo = nodo.parent

    return miglior_nodo


def estrai_annunci_html(html):

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

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True
            )
        )

        link = normalizza_link(
            href
        )

        if not titolo:

            continue

        if link_da_escludere(
            titolo,
            link
        ):

            continue

        if not sembra_link_offerta(
            titolo,
            link
        ):

            continue

        contenitore = trova_contenitore_offerta(
            elemento
        )

        testo_contenitore = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True
            )
        )

        testo_completo = normalizza_testo(
            titolo
            + " "
            + testo_contenitore
            + " "
            + link
        )

        if link not in annunci:

            annunci[
                link
            ] = {
                "titolo": titolo,
                "link": link,
                "testo": testo_contenitore,
                "area_biomedica": contiene_area_biomedica(
                    testo_completo
                ),
                "docenza": contiene_docenza(
                    testo_completo
                ),
                "tempo_indeterminato": (
                    contiene_tempo_indeterminato(
                        testo_completo
                    )
                ),
                "contratto_non_prioritario": (
                    contiene_contratto_non_prioritario(
                        testo_completo
                    )
                )
            }

    return list(
        annunci.values()
    )


def stampa_annunci(annunci):

    print(
        "\nANNUNCI POTENZIALMENTE UTILI:",
        len(annunci)
    )

    for numero, annuncio in enumerate(
        annunci[:50],
        start=1
    ):

        print(
            "\n========================================"
        )

        print(
            "ANNUNCIO:",
            numero
        )

        print(
            "========================================"
        )

        print(
            "TITOLO:",
            annuncio["titolo"]
        )

        print(
            "AREA BIOMEDICA:",
            annuncio["area_biomedica"]
        )

        print(
            "DOCENZA/INSEGNAMENTO:",
            annuncio["docenza"]
        )

        print(
            "TEMPO INDETERMINATO:",
            annuncio["tempo_indeterminato"]
        )

        print(
            "CONTRATTO NON PRIORITARIO:",
            annuncio["contratto_non_prioritario"]
        )

        print(
            "LINK:",
            annuncio["link"]
        )

        print(
            "TESTO:",
            annuncio["testo"][:1800]
        )


def stampa_form(
    soup
):

    forms = soup.find_all(
        "form"
    )

    print(
        "\nFORM TROVATI:",
        len(forms)
    )

    for numero, form in enumerate(
        forms[:20],
        start=1
    ):

        print(
            f"\nFORM {numero}"
        )

        print(
            "ACTION:",
            form.get(
                "action"
            )
        )

        print(
            "METHOD:",
            form.get(
                "method"
            )
        )

        for campo in form.find_all(
            ["input", "select"]
        )[:30]:

            print(
                "CAMPO:",
                campo.get(
                    "name"
                ),
                "VALORE:",
                campo.get(
                    "value"
                )
            )


def stampa_script_utili(
    soup
):

    totale = 0

    print(
        "\nSCRIPT POTENZIALMENTE UTILI:"
    )

    for script in soup.find_all(
        "script"
    ):

        src = script.get(
            "src",
            ""
        )

        contenuto = script.string or ""

        testo_script = (
            src
            + " "
            + contenuto
        ).lower()

        if not any(
            parola in testo_script
            for parola in [
                "career",
                "job",
                "vacancy",
                "annunci",
                "ajax",
                "api",
                "graphql",
                "search",
                "filter"
            ]
        ):

            continue

        totale += 1

        print(
            "\nSRC:",
            src
        )

        if contenuto:

            print(
                "CONTENUTO:",
                contenuto[:2500]
            )

    print(
        "\nTOTALE SCRIPT UTILI:",
        totale
    )


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== DIAGNOSTICA GEMELLI IRCCS ===\n"
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

testo = normalizza_testo(
    soup.get_text(
        " ",
        strip=True
    )
)

print(
    "\nPRIMI 5000 CARATTERI DELLA PAGINA:\n"
)

print(
    testo[:5000]
)

annunci = estrai_annunci_html(
    html
)

stampa_annunci(
    annunci
)

print(
    "\nIFRAME TROVATI:",
    len(
        soup.find_all(
            "iframe"
        )
    )
)

for iframe in soup.find_all(
    "iframe"
):

    print(
        "IFRAME:",
        iframe.get(
            "src"
        )
    )

stampa_form(
    soup
)

stampa_script_utili(
    soup
)

print(
    "\n=== FINE DIAGNOSTICA GEMELLI IRCCS ==="
)
