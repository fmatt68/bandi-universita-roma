import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = (
    "https://progetti.unicatt.it"
)

URL_CATTOLICA_ROMA = (
    "https://progetti.unicatt.it/"
    "progetti-ateneo-concorsi-roma"
)


PAROLE_UTILI = [
    "professore",
    "prima fascia",
    "i fascia",
    "ordinario",
    "docente",
    "docenti",
    "docenza",
    "insegnamento",
    "contratto",
    "ricercatore",
    "ricercatori",
    "concorso",
    "procedura",
    "selezione",
    "bando",
    "avviso",
    "manifestazione",
    "meds-",
    "bios-",
    "med/",
    "bio/"
]


def scarica_pagina():

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
        URL_CATTOLICA_ROMA,
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


def normalizza_testo(testo):

    return " ".join(
        testo.split()
    )


def normalizza_link(href):

    return urljoin(
        BASE_URL,
        href
    )


def link_potenzialmente_utile(
    titolo,
    link
):

    testo = (
        titolo
        + " "
        + link
    ).lower()

    return any(
        parola in testo
        for parola in PAROLE_UTILI
    )


def analizza_pagina(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    testo = soup.get_text(
        "\n",
        strip=True
    )

    print(
        "\n=== TESTO PAGINA CATTOLICA ROMA ===\n"
    )

    print(
        testo[:8000]
    )

    print(
        "\n=== LINK POTENZIALMENTE UTILI ===\n"
    )

    links_visti = set()

    totale = 0

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

        if not href:

            continue

        link = normalizza_link(
            href
        )

        if link in links_visti:

            continue

        if not link_potenzialmente_utile(
            titolo,
            link
        ):

            continue

        links_visti.add(
            link
        )

        totale += 1

        print(
            "TITOLO:",
            titolo
        )

        print(
            "LINK:",
            link
        )

        print()

    print(
        "TOTALE LINK POTENZIALMENTE UTILI:",
        totale
    )

    print(
        "\n=== IFRAME TROVATI ===\n"
    )

    iframe = soup.find_all(
        "iframe"
    )

    print(
        "TOTALE IFRAME:",
        len(iframe)
    )

    for elemento in iframe:

        print(
            "IFRAME:",
            elemento.get(
                "src"
            )
        )

    print(
        "\n=== FORM TROVATI ===\n"
    )

    forms = soup.find_all(
        "form"
    )

    print(
        "TOTALE FORM:",
        len(forms)
    )

    for form in forms[:20]:

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

        print()

    print(
        "\n=== SCRIPT POTENZIALMENTE UTILI ===\n"
    )

    totale_script = 0

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
                "concor",
                "bando",
                "docent",
                "ajax",
                "api",
                "json",
                "search",
                "filter"
            ]
        ):

            continue

        totale_script += 1

        print(
            "SRC:",
            src
        )

        if contenuto:

            print(
                "CONTENUTO:",
                contenuto[:2500]
            )

        print()

    print(
        "TOTALE SCRIPT UTILI:",
        totale_script
    )


# ==========================================
# MAIN
# ==========================================

print(
    "\n=== TEST MONITOR CATTOLICA ROMA ===\n"
)

html = scarica_pagina()

analizza_pagina(
    html
)

print(
    "\n=== FINE TEST CATTOLICA ROMA ===\n"
)
