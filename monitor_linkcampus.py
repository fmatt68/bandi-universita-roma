import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

TESTO_FILE_DA_TROVARE = (
    "1._Bando_PA_D.R._n._2953-2026.pdf"
)


def normalizza_testo(testo):
    return " ".join(
        testo.split()
    )


print("\n=== STRUTTURA HTML LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

elemento_trovato = None

for elemento in soup.find_all(
    "a",
    href=True
):
    href = elemento.get(
        "href",
        ""
    )

    if TESTO_FILE_DA_TROVARE in href:
        elemento_trovato = elemento
        break

if elemento_trovato is None:
    print("DOCUMENTO DI PROVA NON TROVATO")
else:
    link = urljoin(
        URL_LINK_CAMPUS,
        elemento_trovato.get(
            "href",
            ""
        )
    )

    print("DOCUMENTO TROVATO")
    print(
        "Titolo:",
        normalizza_testo(
            elemento_trovato.get_text(
                " ",
                strip=True
            )
        )
    )
    print("Link:", link)

    nodo = elemento_trovato

    print("\n=== CONTENITORI HTML ===")

    for livello in range(12):
        nodo = nodo.parent

        if nodo is None:
            break

        nome = nodo.name or "senza-nome"

        identificativo = nodo.get(
            "id",
            ""
        )

        classi = nodo.get(
            "class",
            []
        )

        if isinstance(
            classi,
            list
        ):
            classi = " ".join(
                classi
            )

        testo = normalizza_testo(
            nodo.get_text(
                " ",
                strip=True
            )
        )

        print(
            "\n----------------------------------------"
        )
        print("LIVELLO:", livello + 1)
        print("ELEMENTO:", nome)
        print("ID:", identificativo or "nessuno")
        print("CLASSI:", classi or "nessuna")
        print("LUNGHEZZA TESTO:", len(testo))
        print("NUMERO LINK:", len(nodo.find_all("a")))
        print("ANTEPRIMA:", testo[:1000])

print("\n=== FINE STRUTTURA HTML ===")
