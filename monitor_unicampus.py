import json
import re

from html import unescape
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = (
    "https://www.unicampus.it"
)


PAGINE_UNICAMPUS = [
    {
        "nome": (
            "Professori I e II fascia "
            "- Procedure selettive"
        ),
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
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "professori-i-e-ii-procedure-valutative/"
        )
    },
    {
        "nome": (
            "Docenti a contratto"
        ),
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "docenti-a-contratto/"
        )
    },
    {
        "nome": (
            "Manifestazioni di interesse"
        ),
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
        "url": (
            "https://www.unicampus.it/ateneo/concorsi/"
            "manifestazioni-di-interesse-foundation-year/"
        )
    }
]


PAROLE_DIAGNOSTICHE = [
    "/concorso/",
    "wp-json",
    "admin-ajax",
    "ajax",
    "graphql",
    "loadmore",
    "load-more",
    "in-atto",
    "in_atto",
    "ordinamento",
    "ord/01_26",
    "ord/02_26",
    "meds-13",
    "bios-11"
]


def scarica_pagina(url):

    headers = {
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

    risposta = requests.get(
        url,
        headers=headers,
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


def normalizza_link(link):

    link = unescape(
        link
    )

    link = link.replace(
        "\\/",
        "/"
    )

    return urljoin(
        BASE_URL,
        link
    )


def estrai_link_concorso(html):

    links = []

    pattern_links = [
        r"""https?://[^"'\\\s]+/concorso/[^"'\\\s<]+""",
        r"""[^"']*/concorso/[^"']+["']""",
        r"""\\?[^"']*\\/concorso\\/[^"']+\\?["']"""
    ]

    for pattern in pattern_links:

        risultati = re.findall(
            pattern,
            html,
            flags=re.IGNORECASE
        )

        for risultato in risultati:

            if isinstance(
                risultato,
                tuple
            ):

                risultato = risultato[0]

            link = normalizza_link(
                risultato
            )

            link = link.rstrip(
                "\\"
            )

            if link not in links:

                links.append(
                    link
                )

    return links


def stampa_elemento_in_atto(
    soup
):

    trovati = soup.find_all(
        string=re.compile(
            r"^\s*In atto\s*$",
            re.IGNORECASE
        )
    )

    print(
        "\nELEMENTI HTML CONTENENTI 'IN ATTO':",
        len(trovati)
    )

    for indice, testo in enumerate(
        trovati[:3],
        start=1
    ):

        print(
            f"\n--- ELEMENTO IN ATTO {indice} ---"
        )

        nodo = testo.parent

        print(
            str(nodo)[:3000]
        )

        print(
            "\n--- CONTENITORE PADRE ---"
        )

        if nodo.parent is not None:

            print(
                str(nodo.parent)[:5000]
            )


def stampa_script_utili(
    soup
):

    print(
        "\nSCRIPT POTENZIALMENTE UTILI:\n"
    )

    totale = 0

    for script in soup.find_all(
        "script"
    ):

        sorgente = script.get(
            "src",
            ""
        )

        contenuto = script.string or ""

        testo_script = (
            sorgente
            + " "
            + contenuto
        )

        testo_lower = testo_script.lower()

        if not any(
            parola in testo_lower
            for parola in [
                "ajax",
                "concorso",
                "concorsi",
                "load",
                "filter",
                "wp-json",
                "api"
            ]
        ):

            continue

        totale += 1

        print(
            "SRC:",
            sorgente
        )

        if contenuto:

            print(
                "CONTENUTO:",
                contenuto[:2000]
            )

        print()

    print(
        "TOTALE SCRIPT UTILI:",
        totale
    )


def stampa_iframe(
    soup
):

    iframe = soup.find_all(
        "iframe"
    )

    print(
        "\nIFRAME TROVATI:",
        len(iframe)
    )

    for elemento in iframe:

        print(
            "SRC:",
            elemento.get(
                "src"
            )
        )


def stampa_attributi_data(
    soup
):

    risultati = []

    for elemento in soup.find_all(
        True
    ):

        attributi_data = {
            nome: valore
            for nome, valore in elemento.attrs.items()
            if nome.startswith(
                "data-"
            )
        }

        if not attributi_data:

            continue

        testo_attributi = json.dumps(
            attributi_data,
            ensure_ascii=False,
            default=str
        ).lower()

        if not any(
            parola in testo_attributi
            for parola in [
                "concor",
                "ajax",
                "load",
                "filter",
                "atto",
                "post"
            ]
        ):

            continue

        risultati.append(
            {
                "tag": elemento.name,
                "attributi": attributi_data
            }
        )

    print(
        "\nATTRIBUTI DATA POTENZIALMENTE UTILI:",
        len(risultati)
    )

    for risultato in risultati[:30]:

        print(
            "TAG:",
            risultato["tag"]
        )

        print(
            "ATTRIBUTI:",
            risultato["attributi"]
        )

        print()


def cerca_parole_html(
    html
):

    html_lower = html.lower()

    print(
        "\nRICERCA PAROLE NELL'HTML GREZZO:\n"
    )

    for parola in PAROLE_DIAGNOSTICHE:

        posizione = html_lower.find(
            parola.lower()
        )

        print(
            f"{parola}:",
            posizione
        )

        if posizione != -1:

            inizio = max(
                0,
                posizione - 300
            )

            fine = min(
                len(html),
                posizione + 1000
            )

            print(
                html[inizio:fine]
            )

            print()


def analizza_pagina(
    nome,
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    print(
        "\n========================================"
    )

    print(
        "SEZIONE:",
        nome
    )

    print(
        "========================================"
    )

    links_concorso = estrai_link_concorso(
        html
    )

    print(
        "\nLINK /concorso/ TROVATI:",
        len(links_concorso)
    )

    for link in links_concorso[:50]:

        print(
            link
        )

    stampa_elemento_in_atto(
        soup
    )

    stampa_iframe(
        soup
    )

    stampa_attributi_data(
        soup
    )

    stampa_script_utili(
        soup
    )

    cerca_parole_html(
        html
    )


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== DIAGNOSTICA CAMPUS BIO-MEDICO ===\n"
)

for pagina in PAGINE_UNICAMPUS:

    print(
        "\n\nAPERTURA SEZIONE:",
        pagina["nome"]
    )

    try:

        html = scarica_pagina(
            pagina["url"]
        )

        analizza_pagina(
            pagina["nome"],
            html
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

print(
    "\n=== FINE DIAGNOSTICA CAMPUS BIO-MEDICO ===\n"
)
