import re
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


PAGINE_ROMATRE = [
    {
        "nome": (
            "Ateneo - Concorsi personale "
            "docente e ricercatore"
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
            "Dipartimento di Scienze "
            "- Bandi e concorsi"
        ),
        "tipo": "docenza",
        "url": (
            "https://scienze.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
        ),
    },
    {
        "nome": (
            "Dipartimento di Scienze "
            "- Incarichi di insegnamento"
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
            "Dipartimento di Matematica e Fisica "
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
            "Ingegneria Civile, Informatica "
            "e Tecnologie Aeronautiche"
        ),
        "tipo": "docenza",
        "url": (
            "https://ingegneriacivileinformaticatecnologieaeronautiche."
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
    "chiamata di professore di prima fascia",
    "chiamata di professori di prima fascia",
]


PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "professori a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento di incarichi di insegnamento",
    "conferimento incarichi di insegnamento",
    "incarico didattico",
    "incarichi didattici",
    "didattica integrativa",
    "supporto alla didattica",
    "attivita didattica",
    "attività didattica",
    "selezione per titoli",
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
]


PAROLE_RICOGNIZIONE_INTERNA = [
    "ricognizione interna",
    "personale interno",
    "personale in servizio presso",
    "risorse interne all'ateneo",
    "risorse interne all’ateneo",
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


def e_link_documento(link):

    link_lower = link.lower()

    indicatori = [
        ".pdf",
        ".doc",
        ".docx",
        "download.aspx",
        "?hd=",
    ]

    return any(
        indicatore in link_lower
        for indicatore in indicatori
    )


def e_link_potenzialmente_utile(
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

    if contiene_parola(
        titolo,
        PAROLE_ACCESSORIE,
    ):

        return False

    return any(
        [
            contiene_parola(
                testo,
                PAROLE_PRIMA_FASCIA,
            ),
            contiene_parola(
                testo,
                PAROLE_DOCENZA,
            ),
            contiene_parola(
                testo,
                PAROLE_AREA,
            ),
        ]
    )


def trova_contenitore(elemento):

    nodo = elemento

    miglior_nodo = elemento.parent

    for _ in range(7):

        if nodo is None:

            break

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True,
            )
        )

        if (
            testo
            and len(testo) <= 4000
        ):

            miglior_nodo = nodo

        contiene_tipologia = (
            contiene_parola(
                testo,
                PAROLE_DOCENZA,
            )
            or contiene_parola(
                testo,
                PAROLE_PRIMA_FASCIA,
            )
        )

        if (
            contiene_tipologia
            and len(testo) <= 4000
        ):

            return nodo

        nodo = nodo.parent

    return miglior_nodo


def estrai_scadenze(testo):

    risultati = []

    patterns = [
        re.compile(
            r"scadenza"
            r"(?:\s+presentazione\s+(?:della\s+)?domanda)?"
            r"\s*:?\s*"
            r"(\d{1,2}/\d{1,2}/\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"scadenza"
            r"(?:\s+presentazione\s+(?:della\s+)?domanda)?"
            r"\s*:?\s*"
            r"(\d{1,2}\s+(?:"
            + MESI_ITALIANI
            + r")\s+\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"entro\s+(?:e\s+non\s+oltre\s+)?"
            r"(?:il\s+giorno\s+)?"
            r"(\d{1,2}\s+(?:"
            + MESI_ITALIANI
            + r")\s+\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"termine\s+invio\s+domande"
            r"\s*:?\s*"
            r"(?:ore\s+\d{1,2}[:.]\d{2}\s+del\s+)?"
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

    risultati = []

    links_visti = set()

    for elemento in soup.find_all(
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

        contenitore = trova_contenitore(
            elemento
        )

        contesto = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True,
            )
        )

        if not e_link_potenzialmente_utile(
            titolo,
            contesto,
            link,
        ):

            continue

        links_visti.add(
            link
        )

        testo_completo = normalizza_testo(
            titolo
            + " "
            + contesto
            + " "
            + link
        )

        risultati.append(
            {
                "titolo": titolo,
                "link": link,
                "documento": e_link_documento(
                    link
                ),
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
        "LINK PERTINENTI TROVATI:",
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
            "DOCUMENTO:",
            risultato["documento"],
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
    "\n=== DIAGNOSTICA ROMA TRE ===\n"
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
    "\nTOTALE LINK PERTINENTI:",
    totale,
)

print(
    "\n=== FINE DIAGNOSTICA ROMA TRE ==="
)
