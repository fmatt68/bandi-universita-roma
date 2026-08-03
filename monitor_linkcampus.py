import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)


def normalizza_testo(testo):
    return " ".join(
        str(testo).split()
    )


def raccogli_testi_precedenti(
    elemento,
    massimo=20
):
    testi = []

    for precedente in elemento.previous_elements:
        if not isinstance(
            precedente,
            NavigableString
        ):
            continue

        testo = normalizza_testo(
            precedente
        )

        if not testo:
            continue

        if testo in testi:
            continue

        testi.append(
            testo
        )

        if len(testi) >= massimo:
            break

    return testi


print("\n=== RICERCA PRIMA FASCIA LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

candidati = []

for elemento in soup.find_all(
    "a",
    href=True
):
    href = elemento.get(
        "href",
        ""
    )

    href_minuscolo = href.lower()

    if "i_ii_fascia" not in href_minuscolo:
        continue

    if ".pdf" not in href_minuscolo:
        continue

    titolo_link = normalizza_testo(
        elemento.get_text(
            " ",
            strip=True
        )
    )

    if (
        "bando" not in titolo_link.lower()
        and "bando" not in href_minuscolo
    ):
        continue

    testi_precedenti = raccogli_testi_precedenti(
        elemento,
        massimo=20
    )

    contesto = normalizza_testo(
        " ".join(
            testi_precedenti
        )
    )

    contesto_minuscolo = contesto.lower()

    prima_fascia = any(
        espressione in contesto_minuscolo
        for espressione in [
            "professore universitario di prima fascia",
            "professore di prima fascia",
            "professoressa di prima fascia",
            "professore ordinario",
            "professoressa ordinaria"
        ]
    )

    seconda_fascia = any(
        espressione in contesto_minuscolo
        for espressione in [
            "professore universitario di seconda fascia",
            "professore di seconda fascia",
            "professoressa di seconda fascia",
            "professore associato",
            "professoressa associata"
        ]
    )

    if not prima_fascia:
        continue

    if seconda_fascia:
        continue

    candidati.append(
        {
            "titolo_link": titolo_link,
            "link": urljoin(
                URL_LINK_CAMPUS,
                href
            ),
            "testi_precedenti": testi_precedenti
        }
    )

print(
    "Possibili bandi di prima fascia:",
    len(candidati)
)

print(
    "\n=== PRIMI 10 CANDIDATI ==="
)

for numero, candidato in enumerate(
    candidati[:10],
    start=1
):
    print(
        "\n========================================"
    )
    print(
        "CANDIDATO",
        numero
    )
    print(
        "========================================"
    )
    print(
        "Titolo del link:",
        candidato["titolo_link"]
    )
    print(
        "Link:",
        candidato["link"]
    )

    print(
        "\nTesti precedenti:"
    )

    for posizione, testo in enumerate(
        candidato["testi_precedenti"],
        start=1
    ):
        print(
            posizione,
            "-",
            testo[:1200]
        )

print(
    "\n=== FINE RICERCA PRIMA FASCIA ==="
)
