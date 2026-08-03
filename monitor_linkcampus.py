import requests
from bs4 import BeautifulSoup


URL_LINK_CAMPUS = (
    "https://unilink.it/ateneo/bandi-e-concorsi/"
)


print("\n=== TEST LINK CAMPUS UNIVERSITY ===\n")

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

titolo_pagina = soup.title

if titolo_pagina:
    print("Titolo della pagina:", titolo_pagina.get_text(strip=True))
else:
    print("Titolo della pagina non trovato")

print("\n=== FINE TEST LINK CAMPUS ===")
