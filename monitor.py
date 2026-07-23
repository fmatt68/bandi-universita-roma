import requests
from bs4 import BeautifulSoup
import re

url = "https://web.uniroma1.it/trasparenza/dettaglio_bando_albo/245584"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

for a in soup.find_all("a"):

    valore = str(a.get("href"))

    if "sites/default/files" not in valore:
        continue

    match = re.search(
        r'href="(https://web\.uniroma1\.it/trasparenza/sites/default/files/[^"]+\.pdf)"',
        valore
    )

    if match:
        print("PDF PULITO:")
        print(match.group(1))
