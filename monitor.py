import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

testo = soup.get_text("\n")

righe = testo.splitlines()

for riga in righe:
    riga = riga.strip()

    if len(riga) > 30:
        print(riga)
