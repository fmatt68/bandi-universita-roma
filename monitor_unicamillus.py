import requests

from bs4 import BeautifulSoup


URL_UNICAMILLUS = (
    "https://unicamillus.org/lavora-con-noi/bandi-docenti/"
)

def scarica_pagina():

    risposta = requests.get(
        URL_UNICAMILLUS,
        timeout=60
    )

    print(
        "Status code:",
        risposta.status_code
    )

    return risposta.text

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
        testo[:1000]
    )

# ==========================================
# MAIN
# ==========================================

html = scarica_pagina()

analizza_pagina(
    html
)
