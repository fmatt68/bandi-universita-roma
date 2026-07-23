import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

testo = soup.get_text("\n")

righe = []

for r in testo.splitlines():
    r = r.strip()
    if r:
        righe.append(r)

for i, riga in enumerate(righe[:300]):
    if "Instructor per corsi di preparazione esami IELTS" in riga:
        print("=== INIZIO BLOCCO ===")

        for j in range(i, min(i + 15, len(righe))):
            print(righe[j])

        print("=== FINE BLOCCO ===")
