import requests
from bs4 import BeautifulSoup
import re

url = "https://web.uniroma1.it/trasparenza/dettaglio_bando_albo/245584"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

for a in soup.find_all("a"):

    href = a.get("href")

    if not href:
        continue

    href = str(href)

    match = re.search(r'https://[^"]+\.pdf', href)

    if match:
        print("PDF TROVATO:")
        print(match.group(0))
