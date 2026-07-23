import requests
from bs4 import BeautifulSoup

url = "https://unicamillus.org/lavora-con-noi/bandi-docenti/"

r = requests.get(url, timeout=30)

print("STATUS:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")

for a in soup.find_all("a"):

    href = a.get("href")
    testo = a.get_text(" ", strip=True)

    if href and testo:

        print("TESTO:", testo[:100])
        print("LINK:", href)
        print()
