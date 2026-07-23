import requests
from bs4 import BeautifulSoup

url = "https://unicamillus.org/lavora-con-noi/bandi-docenti/"

html = requests.get(
    url,
    timeout=30
).text

soup = BeautifulSoup(
    html,
    "html.parser"
)

for a in soup.find_all("a"):

    href = a.get("href", "")

    if ".pdf" in href.lower():

        print(href)
