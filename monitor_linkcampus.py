import requests
from bs4 import BeautifulSoup


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

PAROLE_DA_CERCARE = [
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
    "affidamento di insegnamenti",
    "affidamenti di insegnamenti",
    "contratto di insegnamento",
    "contratti di insegnamento",
    "attività didattica",
    "attivita didattica",
    "attività didattiche",
    "attivita didattiche",
    "collaborazione didattica",
    "collaborazioni didattiche",
    "didattica integrativa",
]


def normalizza_testo(testo):
    return " ".join(
        str(testo).split()
    )


print("\n=== TERMINI DOCENZA NELLA PAGINA LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

for elemento in soup.find_all(
    [
        "script",
        "style",
        "header",
        "footer",
        "nav"
    ]
):
    elemento.decompose()

testo_pagina = normalizza_testo(
    soup.get_text(
        " ",
        strip=True
    )
)

testo_minuscolo = testo_pagina.lower()

risultati = []

for espressione in PAROLE_DA_CERCARE:
    posizione_iniziale = 0
    occorrenze = 0

    while True:
        posizione = testo_minuscolo.find(
            espressione,
            posizione_iniziale
        )

        if posizione == -1:
            break

        occorrenze += 1

        inizio_contesto = max(
            0,
            posizione - 350
        )

        fine_contesto = min(
            len(testo_pagina),
            posizione + len(espressione) + 650
        )

        contesto = testo_pagina[
            inizio_contesto:fine_contesto
        ]

        risultati.append(
            {
                "espressione": espressione,
                "occorrenza": occorrenze,
                "contesto": contesto
            }
        )

        posizione_iniziale = (
            posizione
            + len(espressione)
        )

print(
    "Occorrenze complessive trovate:",
    len(risultati)
)

print(
    "\n=== RISULTATI ==="
)

for numero, risultato in enumerate(
    risultati[:30],
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
        "Espressione:",
        risultato["espressione"]
    )
    print(
        "Occorrenza:",
        risultato["occorrenza"]
    )
    print(
        "Contesto:",
        risultato["contesto"]
    )

print(
    "\n=== FINE RICERCA TERMINI DOCENZA ==="
)
