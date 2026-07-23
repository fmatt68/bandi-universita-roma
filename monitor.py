import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/dettaglio_bando_albo/245584"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

testo = soup.get_text("\n")

print(testo[:5000])
