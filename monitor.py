import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL_SAPIENZA = (
    "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
    "?field_user_centro_spesa_ugov_tid=All"
    "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
    "&field_bis_sc_e_ssd_tid=All"
    "&keys="
    "&field_bis_gsd_ssd_target_id=All"
)

response = requests.get(URL_SAPIENZA)
soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")

oggi = datetime.now()

contatore = 0

print("INIZIO ANALISI PDF\n")

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

        dettaglio_soup = BeautifulSoup(
            dettaglio.text,
            "html.parser"
        )

        testo = dettaglio_soup.get_text("\n")

        righe = [
            r.strip()
            for r in testo.splitlines()
            if r.strip()
        ]

        data_scadenza = None

        for i, riga in enumerate(righe):

            if riga == "Data scadenza:" and i + 1 < len(righe):
                data_scadenza = righe[i + 1]
                break

        if not data_scadenza:
            continue

        try:
            data_scadenza_dt = datetime.strptime(
                data_scadenza,
                "%d-%m-%Y"
            )
        except Exception:
            continue

        if data_scadenza_dt < oggi:
            continue

        print("\n================================")
        print("TITOLO:", titolo)
        print("SCADENZA:", data_scadenza)

        pdf_presenti = False

        for a in dettaglio_soup.find_all("a"):

            pdf_href = a.get("href")

            if not pdf_href:
                continue

            pdf_href = str(pdf_href)

            if ".pdf" in pdf_href.lower():

                pdf_presenti = True

                print("PDF:", pdf_href)

        if not pdf_presenti:
            print("NESSUN PDF TROVATO")

        contatore += 1

        if contatore >= 10:
            break

    except Exception as e:
        print("ERRORE:", e)

print("\nFINE ANALISI PDF")
