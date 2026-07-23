import requests
from pypdf import PdfReader
from io import BytesIO

PRIORITA_ALTA = [
    "ematologia",
    "oncologia",
    "immunologia",
    "genetica",
    "biologia",
    "biologia molecolare",
    "biologia cellulare",
    "scienze biologiche",
    "biotecnologie"
]

PRIORITA_MEDIA = [
    "biochimica",
    "patologia generale",
    "medicina di laboratorio",
    "tecniche di laboratorio biomedico"
]

PRIORITA_BASSA = [
    "reumatologia",
    "fisiologia",
    "istologia"
]

pdf_url = "https://web.uniroma1.it/trasparenza/sites/default/files/Bando_7-2026_Instructor_IELTS.pdf"

response = requests.get(pdf_url)

print("Download PDF:", response.status_code)

reader = PdfReader(BytesIO(response.content))

testo = ""

for pagina in reader.pages:
    testo += pagina.extract_text() or ""

testo = testo.lower()

trovate = []

for parola in PRIORITA_ALTA:
    if parola in testo:
        trovate.append(("ALTA", parola))

for parola in PRIORITA_MEDIA:
    if parola in testo:
        trovate.append(("MEDIA", parola))

for parola in PRIORITA_BASSA:
    if parola in testo:
        trovate.append(("BASSA", parola))

print("\nPAROLE TROVATE\n")

if trovate:
    for priorita, parola in trovate:
        print(f"[{priorita}] {parola}")
else:
    print("Nessuna parola chiave trovata")
