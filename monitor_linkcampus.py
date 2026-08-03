import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)

TESTO_FILE_DA_TROVARE = (
    "1._Bando_PA_D.R._n._2953-2026.pdf"
)


def normalizza_testo(testo):
    return " ".join(
        str(testo).split()
    )


print("\n=== ELEMENTI PRECEDENTI LINK CAMPUS ===\n")

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
    print("DOCUMENTO TROVATO")
    print(
        "Titolo del link:",
        normalizza_testo(
            elemento_trovato.get_text(
                " ",
                strip=True
            )
        )
    )

    elementi_precedenti = []

    for elemento in elemento_trovato.previous_elements:
        if isinstance(
            elemento,
            NavigableString
        ):
            testo = normalizza_testo(
                elemento
            )

            if not testo:
                continue

            elementi_precedenti.append(
                {
                    "tipo": "testo",
                    "nome": "testo",
                    "classi": "",
                    "testo": testo
                }
            )

        elif isinstance(
            elemento,
            Tag
        ):
            if elemento.name not in [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "p",
                "strong"
            ]:
                continue

            testo = normalizza_testo(
                elemento.get_text(
                    " ",
                    strip=True
                )
            )

            if not testo:
                continue

            classi = elemento.get(
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

            elementi_precedenti.append(
                {
                    "tipo": "tag",
                    "nome": elemento.name,
                    "classi": classi,
                    "testo": testo
                }
            )

        if len(
            elementi_precedenti
        ) >= 30:
            break

    print(
        "\n=== 30 ELEMENTI PRECEDENTI ==="
    )

    for numero, elemento in enumerate(
        elementi_precedenti,
        start=1
    ):
        print(
            "\n----------------------------------------"
        )
        print(
            "POSIZIONE PRIMA DEL LINK:",
            numero
        )
        print(
            "TIPO:",
            elemento["tipo"]
        )
        print(
            "ELEMENTO:",
            elemento["nome"]
        )
        print(
            "CLASSI:",
            elemento["classi"]
            or "nessuna"
        )
        print(
            "TESTO:",
            elemento["testo"][:1500]
        )

print("\n=== FINE ELEMENTI PRECEDENTI ===")
