import requests
from io import BytesIO
from pypdf import PdfReader

pdf_url = "https://unicamillus.org/wp-content/uploads/bandi-docenti/2026/dr_58-2026_avviso_manifestazione-di-interesse-confermineto-incarichi-docenti-a-contratto.pdf"

response = requests.get(pdf_url, timeout=60)

print("STATUS:", response.status_code)

reader = PdfReader(BytesIO(response.content))

testo = ""

for pagina in reader.pages:
    testo += pagina.extract_text() or ""

print("\n=== INIZIO TESTO ===\n")
print(testo[:12000])
print("\n=== FINE TESTO ===")
