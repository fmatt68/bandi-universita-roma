import requests

from io import BytesIO
from pypdf import PdfReader

pdf_url = "https://web.uniroma1.it/trasparenza/sites/default/files/1.%20Bando%20incarichi%20docenza%20I%C2%B0%20semestre%20a.a.%202026-2027%20PROT..pdf"

response = requests.get(pdf_url)

reader = PdfReader(
    BytesIO(response.content)
)

testo = ""

for pagina in reader.pages:

    testo += pagina.extract_text() or ""

print(testo[:10000])
