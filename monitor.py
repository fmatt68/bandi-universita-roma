import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/dettaglio_bando_albo/245584"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")

for link in links:

    testo = link.get_text(" ", strip=True)
    href = link.get("href")

    if testo or href:

        print("TESTO:", testo)
        print("LINK:", href)
        print("---")
