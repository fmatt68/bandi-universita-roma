import requests
from bs4 import BeautifulSoup

url = "https://web.uniroma1.it/trasparenza/dettaglio_bando_albo/245584"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

for a in soup.find_all("a"):

    href = a.get("href")

    if href:
        print(repr(href))
