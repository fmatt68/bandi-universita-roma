import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

strongs = soup.find_all("strong")

oggi = datetime.now()

print("\nBANDI NON SCADUTI\n")

for i in range(len(strongs)):

    titolo = strongs[i].get_text(" ", strip=True)

    if titolo in [
        "",
        "Data pubblicazione bando:",
        "Data scadenza bando:",
        "codice bando:",
        "Filtra",
        "Bandi di concorso pubblicati antecedentemente all'8 febbraio 2016"
    ]:
        continue

    try:

        data_scadenza = strongs[i + 3].parent.get_text(
            " ",
            strip=True
        ).replace(
            "Data scadenza bando:",
            ""
        ).strip()

        data_scadenza_dt = datetime.strptime(
            data_scadenza,
            "%d-%m-%Y"
        )

        if data_scadenza_dt >= oggi:

            print("TITOLO:", titolo)
            print("SCADENZA:", data_scadenza)
            print()

    except Exception:
        pass
