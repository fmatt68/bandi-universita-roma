import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

PAROLE_DA_CERCARE = [
    "prima fascia",
    "professore ordinario",
    "professoressa ordinaria",
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
]


def normalizza_testo(testo):
    return " ".join(
        testo.split()
    )


print("\n=== DIAGNOSTICA MIRATA LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

print("Pagina raggiunta correttamente")
print("Status code:", risposta.status_code)

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

    contenitore = elemento

    for livello in range(8):
        if contenitore.parent is None:
            break

        contenitore = contenitore.parent

        testo_contenitore = normalizza_testo(
            contenitore.get_text(
                " ",
                strip=True
            )
        )

        if (
            len(testo_contenitore) >= 80
            and len(testo_contenitore) <= 5000
        ):
            break

    testo_completo = normalizza_testo(
        titolo_link
        + " "
        + testo_contenitore
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
        for parola in PAROLE_DA_CERCARE
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
            "contesto": testo_contenitore[:2500]
        }
    )

print(
    "\nDocumenti potenzialmente pertinenti:",
    len(risultati)
)

print(
    "\n=== PRIMI 40 RISULTATI MIRATI ==="
)

for numero, risultato in enumerate(
    risultati[:40],
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
        "Contesto:",
        risultato["contesto"]
    )

print(
    "\n=== FINE DIAGNOSTICA MIRATA ==="
)
