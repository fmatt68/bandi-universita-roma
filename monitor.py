import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pypdf import PdfReader
from io import BytesIO

PAROLE_CHIAVE = [
    "ematologia",
    "oncologia",
    "immunologia",
    "genetica",
    "biologia",
    "biologia molecolare",
    "biologia cellulare",
    "scienze biologiche",
    "biotecnologie",
    "biochimica",
    "patologia generale",
    "medicina di laboratorio",
    "tecniche di laboratorio biomedico",
    "reumatologia",
    "fisiologia",
    "istologia"
]

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")

oggi = datetime.now()

print("INIZIO ANALISI BANDI\n")

contatore = 0

for link in links:

    titolo = link.get_text(" ", strip=True)
    href = link.get("href")

    if not href:
        continue

    if "/trasparenza/dettaglio_bando_albo/" not in href:
        continue

    dettaglio_url = "https://web.uniroma1.it" + href

    try:

        dettaglio = requests.get(dettaglio_url)
        dettaglio_soup = BeautifulSoup(dettaglio.text, "html.parser")

        testo_dettaglio = dettaglio_soup.get_text("\n")

        if "Data scadenza:" not in testo_dettaglio:
            continue

        righe = [r.strip() for r in testo_dettaglio.splitlines() if r.strip()]

        data_scadenza = None

        for i, riga in enumerate(righe):

            if riga == "Data scadenza:" and i + 1 < len(righe):
                data_scadenza = righe[i + 1]
                break

        if not data_scadenza:
            continue

        data_scadenza_dt = datetime.strptime(
            data_scadenza,
            "%d-%m-%Y"
        )

        if data_scadenza_dt < oggi:
            continue

        pdf_links = dettaglio_soup.find_all("a")

        trovato = False

        for pdf_link in pdf_links:

            pdf_href = pdf_link.get("href")

            if not pdf_href:
                continue

            if "sites/default/files" not in str(pdf_href):
                continue

            if ".pdf" not in str(pdf_href).lower():
                continue

            pdf_response = requests.get(pdf_href)

            reader = PdfReader(BytesIO(pdf_response.content))

            testo_pdf = ""

            for pagina in reader.pages:
                testo_pdf += pagina.extract_text() or ""

            testo_pdf = testo_pdf.lower()

            for parola in PAROLE_CHIAVE:

                if parola in testo_pdf:

                    print("================================")
                    print("TITOLO:", titolo)
                    print("SCADENZA:", data_scadenza)
                    print("PAROLA TROVATA:", parola)
                    print("PDF:", pdf_href)
                    print()

                    trovato = True
                    break

            if trovato:
                break

        contatore += 1

        if contatore >= 15:
            break

    except Exception:
        pass

print("FINE ANALISI")
