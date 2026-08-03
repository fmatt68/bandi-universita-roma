import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "insegnamento a contratto",
    "insegnamenti a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "incarico di docenza",
    "incarichi di docenza",
    "conferimento di insegnamenti",
    "conferimento degli insegnamenti",
]


def normalizza_testo(testo):
    return " ".join(
        str(testo).split()
    )


def raccogli_testi_precedenti(
    elemento,
    massimo=25
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


print("\n=== RICERCA DOCENZE LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

risultati = []
link_gia_visti = set()

for elemento in soup.find_all(
    "a",
    href=True
):
    href = elemento.get(
        "href",
        ""
    )

    link = urljoin(
        URL_LINK_CAMPUS,
        href
    )

    link_minuscolo = link.lower()

    if not any(
        estensione in link_minuscolo
        for estensione in [
            ".pdf",
            ".doc",
            ".docx"
        ]
    ):
        continue

    if link in link_gia_visti:
        continue

    titolo_link = normalizza_testo(
        elemento.get_text(
            " ",
            strip=True
        )
    )

    testi_precedenti = raccogli_testi_precedenti(
        elemento,
        massimo=25
    )

    contesto = normalizza_testo(
        " ".join(
            testi_precedenti
        )
    )

    testo_completo = normalizza_testo(
        titolo_link
        + " "
        + contesto
        + " "
        + link.replace(
            "-",
            " "
        ).replace(
            "_",
            " "
        )
    )

    testo_minuscolo = testo_completo.lower()

    parole_trovate = [
        parola
        for parola in PAROLE_DOCENZA
        if parola in testo_minuscolo
    ]

    if not parole_trovate:
        continue

    link_gia_visti.add(
        link
    )

    risultati.append(
        {
            "titolo_link": titolo_link,
            "link": link,
            "parole": parole_trovate,
            "testi_precedenti": testi_precedenti
        }
    )

print(
    "Documenti potenzialmente collegati a docenze:",
    len(risultati)
)

print(
    "\n=== PRIMI 20 RISULTATI ==="
)

for numero, risultato in enumerate(
    risultati[:20],
    start=1
):
    print(
        "\n========================================"
    )
    print(
        "RISULTATO",
        numero
    )
    print(
        "========================================"
    )
    print(
        "Titolo del link:",
        risultato["titolo_link"]
        or "Titolo non presente"
    )
    print(
        "Parole trovate:",
        ", ".join(
            risultato["parole"]
        )
    )
    print(
        "Link:",
        risultato["link"]
    )

    print(
        "\nTesti precedenti:"
    )

    for posizione, testo in enumerate(
        risultato["testi_precedenti"][:15],
        start=1
    ):
        print(
            posizione,
            "-",
            testo[:1000]
        )

print(
    "\n=== FINE RICERCA DOCENZE ==="
)
