import re

from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


PAGINE_ROMATRE = [
    {
        "nome": (
            "Personale docente e ricercatore"
        ),
        "tipo": "professori",
        "url": (
            "https://www.uniroma3.it/servizi/"
            "servizi-al-personale/portale-del-personale/"
            "concorsi-e-selezioni/"
            "concorsi-personale-docente-e-ricercatore/"
        ),
    },
    {
        "nome": (
            "Scienze - Incarichi di insegnamento"
        ),
        "tipo": "docenza",
        "url": (
            "https://scienze.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
            "bandi-per-incarichi-di-insegnamento/"
        ),
    },
    {
        "nome": (
            "Matematica e Fisica "
            "- Incarichi didattici"
        ),
        "tipo": "docenza",
        "url": (
            "https://matematicafisica.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
            "bandi-per-incarichi-di-insegnamento-"
            "e-di-didattica-integrativa/"
        ),
    },
    {
        "nome": (
            "Ingegneria Civile e Informatica "
            "- Bandi e concorsi"
        ),
        "tipo": "docenza",
        "url": (
            "https://"
            "ingegneriacivileinformaticatecnologieaeronautiche."
            "uniroma3.it/dipartimento/bandi-e-concorsi/"
        ),
    },
]


PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore ordinario",
    "professoressa ordinaria",
    "professore di ruolo di prima fascia",
    "professoressa di ruolo di prima fascia",
]


PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "incarico didattico",
    "incarichi didattici",
    "didattica integrativa",
    "supporto alla didattica",
    "attivita didattica",
    "attività didattica",
]


PAROLE_BANDO = [
    "bando",
    "avviso",
    "procedura selettiva",
    "procedura di selezione",
    "selezione pubblica",
    "conferimento di incarichi",
    "conferimento incarichi",
    "ricognizione interna",
    "concorsi (albo pretorio)",
]


PAROLE_AREA = [
    "meds-",
    "medf-",
    "bios-",
    "mvet-",
    "iinf-",
    "phys-",
    "ibio-",
    "bio/",
    "med/",
    "vet/",
    "fis/",
    "ing-inf/",
    "biologia",
    "biotecnologie",
    "biochimica",
    "bioinformatica",
    "fisica",
    "informatica",
    "ingegneria biomedica",
    "bioingegneria",
    "scienze biologiche",
    "scienze della vita",
    "laboratorio",
]


PAROLE_ACCESSORIE = [
    "allegato",
    "fac-simile",
    "fac simile",
    "modello cv",
    "domanda di partecipazione",
    "autocertificazione",
    "esito",
    "graduatoria",
    "vincitori",
    "commissione",
    "verbale",
    "approvazione atti",
    "rettifica",
]


PAROLE_RICOGNIZIONE_INTERNA = [
    "ricognizione interna",
    "personale interno",
    "personale dell'ateneo",
    "personale dell’ateneo",
    "personale in servizio presso",
    "risorse interne all'ateneo",
    "risorse interne all’ateneo",
    "mansioni esigibili da personale dell'ateneo",
    "mansioni esigibili da personale dell’ateneo",
]


MESI_ITALIANI = (
    "gennaio|febbraio|marzo|aprile|maggio|"
    "giugno|luglio|agosto|settembre|ottobre|"
    "novembre|dicembre"
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
            ),
        }
    )

    return sessione


def scarica_pagina(
    sessione,
    url,
):

    risposta = sessione.get(
        url,
        timeout=60,
    )

    print(
        "Status code:",
        risposta.status_code,
    )

    print(
        "URL finale:",
        risposta.url,
    )

    print(
        "Dimensione HTML:",
        len(
            risposta.text
        ),
    )

    risposta.raise_for_status()

    return risposta.text


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


def normalizza_link(
    base_url,
    href,
):

    link = urljoin(
        base_url,
        href,
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
            "",
        )
    )


def contiene_parola(
    testo,
    parole,
):

    testo_lower = testo.lower()

    return any(
        parola in testo_lower
        for parola in parole
    )


def pulisci_pagina(soup):

    selettori = [
        "script",
        "style",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        ".menu",
        ".main-menu",
        ".navigation",
        ".navbar",
        ".breadcrumb",
        ".breadcrumbs",
        ".sidebar",
        ".site-header",
        ".site-footer",
        "[role='navigation']",
        "[aria-label*='menu' i]",
    ]

    for selettore in selettori:

        for elemento in soup.select(
            selettore
        ):

            elemento.decompose()


def trova_contenuto_principale(soup):

    selettori = [
        "main",
        "article",
        "#content",
        "#main-content",
        ".entry-content",
        ".page-content",
        ".content-area",
        "[role='main']",
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
                strip=True,
            )
        )

        if len(testo) >= 50:

            return elemento

    return soup.body or soup


def e_link_documento(link):

    link_lower = link.lower()

    indicatori = [
        ".pdf",
        ".doc",
        ".docx",
        "download.aspx",
        "albopretorio",
        "traspare.com/news/",
        "uniroma3.traspare.com",
    ]

    return any(
        indicatore in link_lower
        for indicatore in indicatori
    )


def testo_locale_link(elemento):

    for nodo in elemento.parents:

        if not isinstance(
            nodo,
            Tag,
        ):

            continue

        if nodo.name in [
            "li",
            "p",
            "section",
            "article",
        ]:

            testo = normalizza_testo(
                nodo.get_text(
                    " ",
                    strip=True,
                )
            )

            if (
                20
                <= len(testo)
                <= 2500
            ):

                return testo

        if nodo.name == "main":

            break

    precedenti = []

    for vicino in elemento.previous_elements:

        if len(precedenti) >= 12:

            break

        if isinstance(
            vicino,
            NavigableString,
        ):

            testo = normalizza_testo(
                vicino
            )

            if testo:

                precedenti.append(
                    testo
                )

    precedenti.reverse()

    successivi = []

    for vicino in elemento.next_elements:

        if len(successivi) >= 12:

            break

        if (
            isinstance(
                vicino,
                Tag,
            )
            and vicino.name == "a"
            and vicino is not elemento
        ):

            href = vicino.get(
                "href",
                "",
            )

            if (
                href
                and e_link_documento(
                    href
                )
            ):

                break

        if isinstance(
            vicino,
            NavigableString,
        ):

            testo = normalizza_testo(
                vicino
            )

            if testo:

                successivi.append(
                    testo
                )

    testo_locale = normalizza_testo(
        " ".join(
            precedenti
            + successivi
        )
    )

    return testo_locale[:3000]


def estrai_scadenze(testo):

    risultati = []

    patterns = [
        re.compile(
            r"scadenza"
            r"(?:\s+presentazione\s+(?:della\s+)?domanda)?"
            r"\s*:?\s*"
            r"(?:entro\s+e\s+non\s+oltre\s+"
            r"(?:il\s+giorno\s+)?)?"
            r"(\d{1,2}/\d{1,2}/\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"scadenza"
            r"(?:\s+presentazione\s+(?:della\s+)?domanda)?"
            r"\s*:?\s*"
            r"(?:entro\s+e\s+non\s+oltre\s+"
            r"(?:il\s+giorno\s+)?)?"
            r"(\d{1,2}\s+(?:"
            + MESI_ITALIANI
            + r")\s+\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"entro\s+e\s+non\s+oltre\s+"
            r"(?:il\s+giorno\s+)?"
            r"(\d{1,2}\s+(?:"
            + MESI_ITALIANI
            + r")\s+\d{4})",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:

        for risultato in pattern.findall(
            testo
        ):

            risultato = normalizza_testo(
                risultato
            )

            if risultato not in risultati:

                risultati.append(
                    risultato
                )

    return risultati


def titolo_accessorio(titolo):

    return contiene_parola(
        titolo,
        PAROLE_ACCESSORIE,
    )


def candidato_utile(
    titolo,
    contesto,
    link,
):

    testo = normalizza_testo(
        titolo
        + " "
        + contesto
        + " "
        + unescape(
            link
        )
    )

    if titolo_accessorio(
        titolo
    ):

        return False

    ha_tipologia = (
        contiene_parola(
            testo,
            PAROLE_BANDO,
        )
        or contiene_parola(
            testo,
            PAROLE_PRIMA_FASCIA,
        )
        or contiene_parola(
            testo,
            PAROLE_DOCENZA,
        )
    )

    ha_link_utile = e_link_documento(
        link
    )

    return (
        ha_tipologia
        and ha_link_utile
    )


def analizza_pagina(
    nome,
    tipo,
    url,
    html,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    pulisci_pagina(
        soup
    )

    contenuto = trova_contenuto_principale(
        soup
    )

    risultati = []

    links_visti = set()

    for elemento in contenuto.find_all(
        "a",
        href=True,
    ):

        href = elemento.get(
            "href"
        )

        if not href:

            continue

        link = normalizza_link(
            url,
            href,
        )

        if link in links_visti:

            continue

        titolo = normalizza_testo(
            elemento.get_text(
                " ",
                strip=True,
            )
        )

        if not titolo:

            continue

        contesto = testo_locale_link(
            elemento
        )

        if not candidato_utile(
            titolo,
            contesto,
            link,
        ):

            continue

        testo_completo = normalizza_testo(
            titolo
            + " "
            + contesto
            + " "
            + link
        )

        links_visti.add(
            link
        )

        risultati.append(
            {
                "titolo": titolo,
                "link": link,
                "prima_fascia": contiene_parola(
                    testo_completo,
                    PAROLE_PRIMA_FASCIA,
                ),
                "docenza": contiene_parola(
                    testo_completo,
                    PAROLE_DOCENZA,
                ),
                "area": contiene_parola(
                    testo_completo,
                    PAROLE_AREA,
                ),
                "ricognizione_interna": contiene_parola(
                    testo_completo,
                    PAROLE_RICOGNIZIONE_INTERNA,
                ),
                "scadenze": estrai_scadenze(
                    testo_completo
                ),
                "contesto": contesto,
            }
        )

    print(
        "\n========================================"
    )

    print(
        "SEZIONE:",
        nome,
    )

    print(
        "TIPO:",
        tipo,
    )

    print(
        "========================================"
    )

    print(
        "CANDIDATI LOCALI TROVATI:",
        len(
            risultati
        ),
    )

    for numero, risultato in enumerate(
        risultati,
        start=1,
    ):

        print(
            "\n----------------------------------------"
        )

        print(
            "RISULTATO:",
            numero,
        )

        print(
            "TITOLO:",
            risultato["titolo"],
        )

        print(
            "PRIMA FASCIA:",
            risultato["prima_fascia"],
        )

        print(
            "DOCENZA:",
            risultato["docenza"],
        )

        print(
            "AREA INTERESSE:",
            risultato["area"],
        )

        print(
            "RICOGNIZIONE INTERNA:",
            risultato["ricognizione_interna"],
        )

        print(
            "SCADENZE:",
            risultato["scadenze"],
        )

        print(
            "LINK:",
            risultato["link"],
        )

        print(
            "CONTESTO:",
            risultato["contesto"][:1600],
        )

    return risultati


# =========================================================
# MAIN
# =========================================================

print(
    "\n=== DIAGNOSTICA ROMA TRE V2 ===\n"
)

sessione = crea_sessione()

totale = 0

for pagina in PAGINE_ROMATRE:

    print(
        "\n\nControllo:",
        pagina["nome"],
    )

    try:

        html = scarica_pagina(
            sessione,
            pagina["url"],
        )

        risultati = analizza_pagina(
            pagina["nome"],
            pagina["tipo"],
            pagina["url"],
            html,
        )

        totale += len(
            risultati
        )

    except Exception as errore:

        print(
            "ERRORE NELLA SEZIONE:",
            pagina["nome"],
        )

        print(
            str(
                errore
            )
        )

print(
    "\nTOTALE CANDIDATI LOCALI:",
    totale,
)

print(
    "\n=== FINE DIAGNOSTICA ROMA TRE V2 ==="
)
