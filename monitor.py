import json
import requests

from io import BytesIO
from pypdf import PdfReader

from datetime import datetime
from bs4 import BeautifulSoup


# ==================================================
# CONFIG
# ==================================================

URL_SAPIENZA = (
    "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
    "?field_user_centro_spesa_ugov_tid=All"
    "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
    "&field_bis_sc_e_ssd_tid=All"
    "&keys="
    "&field_bis_gsd_ssd_target_id=All"
)

KEYWORDS = [
    "biologia",
    "biologia molecolare",
    "biologia cellulare",
    "scienze biologiche",
    "biotecnologie",
    "genetica",
    "genetica medica",
    "immunologia",
    "ematologia",
    "oncologia",
    "biochimica",
    "patologia generale",
    "medicina di laboratorio",
    "laboratorio biomedico",
    "tecniche di laboratorio biomedico",
    "fisiologia",
    "istologia",
    "reumatologia",
]

oggi = datetime.now()


# ==================================================
# PDF
# ==================================================

def leggi_pdf(url):

    try:

        print("SCARICO PDF:", url)

        response = requests.get(
            url,
            timeout=60
        )

        print(
            "STATUS PDF:",
            response.status_code
        )

        reader = PdfReader(
            BytesIO(response.content)
        )

        testo = ""

        for pagina in reader.pages:
            testo += (
                pagina.extract_text()
                or ""
            )

        print(
            "LUNGHEZZA TESTO PDF:",
            len(testo)
        )

        return testo.lower()

    except Exception as e:

        print(
            "ERRORE PDF:",
            str(e)
        )

        return ""


# ==================================================
# PDF URL
# ==================================================

def trova_pdf_url(html):

    risultati = []

    testo = html

    marker = (
        "https://web.uniroma1.it/trasparenza/"
        "sites/default/files/"
    )

    posizione = 0

    while True:

        start = testo.find(
            marker,
            posizione
        )

        if start == -1:
            break

        end = testo.find(
            ".pdf",
            start
        )

        if end == -1:
            break

        pdf = testo[start:end + 4]

        if pdf not in risultati:
            risultati.append(pdf)

        posizione = end + 4

    return risultati


# ==================================================
# MAIN
# ==================================================

print("\n=== TEST COMPLETO PDF ===\n")

pagina = requests.get(
    URL_SAPIENZA,
    timeout=30
)

soup = BeautifulSoup(
    pagina.text,
    "html.parser"
)

analizzati = 0

for link in soup.find_all("a"):

    href = link.get("href")
    titolo = link.get_text(
        " ",
        strip=True
    )

    if not href:
        continue

    if (
        "/trasparenza/dettaglio_bando_albo/"
        not in href
    ):
        continue

    dettaglio_url = (
        "https://web.uniroma1.it" + href
    )

    try:

        dettaglio = requests.get(
            dettaglio_url,
            timeout=30
        )

        html = dettaglio.text

        dettaglio_soup = BeautifulSoup(
            html,
            "html.parser"
        )

        testo = dettaglio_soup.get_text(
            "\n"
        )

        righe = [
            r.strip()
            for r in testo.splitlines()
            if r.strip()
        ]

        data_scadenza = None

        for i, riga in enumerate(righe):

            if (
                riga == "Data scadenza:"
                and i + 1 < len(righe)
            ):
                data_scadenza = (
                    righe[i + 1]
                )
                break

        if not data_scadenza:
            continue

        try:

            data_dt = datetime.strptime(
                data_scadenza,
                "%d-%m-%Y"
            )

        except Exception:
            continue

        if data_dt < oggi:
            continue

        print("\n======================")
        print("TITOLO:", titolo)
        print("SCADENZA:", data_scadenza)

        pdf_urls = trova_pdf_url(
            html
        )

        print(
            "PDF TROVATI:",
            len(pdf_urls)
        )

        if len(pdf_urls) == 0:
            continue

        for pdf_url in pdf_urls:

            testo_pdf = leggi_pdf(
                pdf_url
            )

            for keyword in KEYWORDS:

                if keyword in testo_pdf:

                    print(
                        "MATCH:",
                        keyword
                    )

        analizzati += 1

        if analizzati >= 10:
            break

    except Exception as e:

        print(
            "ERRORE BANDO:",
            titolo
        )

        print(str(e))

print("\n=== FINE TEST ===")
