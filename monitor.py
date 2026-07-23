import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")

for i, link in enumerate(links[:100]):

    testo = link.get_text(" ", strip=True)

    href = link.get("href")

    if testo and href:
        print("-----")
        print("TESTO:", testo)
        print("LINK:", href)
