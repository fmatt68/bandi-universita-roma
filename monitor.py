import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

strongs = soup.find_all("strong")

for i in range(7, 17):
    print("-----")
    print(i)
    print(repr(strongs[i].get_text(" ", strip=True)))

    parent = strongs[i].parent

    print("PARENT:")
    print(parent.get_text(" ", strip=True)[:500])
