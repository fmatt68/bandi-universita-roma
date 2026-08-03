import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)


print("\n=== FILE I E II FASCIA LINK CAMPUS ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

documenti = []
link_gia_visti = set()

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

    link = urljoin(
        URL_LINK_CAMPUS,
        href
    )

    if link in link_gia_visti:
        continue

    link_gia_visti.add(
        link
    )

    titolo = " ".join(
        elemento.get_text(
            " ",
            strip=True
        ).split()
    )

    nome_file = link.rsplit(
        "/",
        1
    )[-1]

    documenti.append(
        {
            "titolo": titolo,
            "nome_file": nome_file,
            "link": link
        }
    )

print(
    "Documenti trovati nella cartella I_II_fascia:",
    len(documenti)
)

print(
    "\n=== ELENCO DOCUMENTI ==="
)

for numero, documento in enumerate(
    documenti,
    start=1
):
    nome_minuscolo = documento[
        "nome_file"
    ].lower()

    indicatori = []

    if "bando_pa" in nome_minuscolo:
        indicatori.append(
            "Possibile professore associato"
        )

    if "bando_po" in nome_minuscolo:
        indicatori.append(
            "Possibile professore ordinario"
        )

    if "ord" in nome_minuscolo:
        indicatori.append(
            "Possibile ordinario"
        )

    if "prima_fascia" in nome_minuscolo:
        indicatori.append(
            "Prima fascia"
        )

    if "i_fascia" in nome_minuscolo:
        indicatori.append(
            "I fascia"
        )

    print(
        "\n----------------------------------------"
    )
    print(
        "DOCUMENTO:",
        numero
    )
    print(
        "Titolo del link:",
        documento["titolo"]
        or "Titolo non presente"
    )
    print(
        "Nome del file:",
        documento["nome_file"]
    )
    print(
        "Indicatori:",
        ", ".join(
            indicatori
        )
        if indicatori
        else "Nessun indicatore nel nome"
    )
    print(
        "Link:",
        documento["link"]
    )

print(
    "\n=== FINE ELENCO DOCUMENTI ==="
)
