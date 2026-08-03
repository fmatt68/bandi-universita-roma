import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)


print("\n=== DIAGNOSTICA LINK CAMPUS UNIVERSITY ===\n")

risposta = requests.get(
    URL_LINK_CAMPUS,
    timeout=60
)

risposta.raise_for_status()

print("Pagina raggiunta correttamente")
print("Status code:", risposta.status_code)
print("URL finale:", risposta.url)
print("Dimensione HTML:", len(risposta.text))

soup = BeautifulSoup(
    risposta.text,
    "html.parser"
)

tutti_i_link = soup.find_all(
    "a",
    href=True
)

documenti = []

for elemento in tutti_i_link:
    href = elemento.get(
        "href",
        ""
    )

    titolo = elemento.get_text(
        " ",
        strip=True
    )

    link = urljoin(
        URL_LINK_CAMPUS,
        href
    )

    link_minuscolo = link.lower()

    if any(
        estensione in link_minuscolo
        for estensione in [
            ".pdf",
            ".doc",
            ".docx"
        ]
    ):
        documenti.append(
            {
                "titolo": titolo,
                "link": link
            }
        )

print("\nCollegamenti complessivi:", len(tutti_i_link))
print("Documenti PDF, DOC o DOCX:", len(documenti))

print("\n=== PRIMI 30 DOCUMENTI INDIVIDUATI ===")

for numero, documento in enumerate(
    documenti[:30],
    start=1
):
    print("\nDOCUMENTO", numero)
    print(
        "Titolo:",
        documento["titolo"]
        or "Titolo non presente"
    )
    print(
        "Link:",
        documento["link"]
    )

print("\n=== FINE DIAGNOSTICA LINK CAMPUS ===")
