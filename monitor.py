import requests
from pypdf import PdfReader
from io import BytesIO

pdf_url = "https://web.uniroma1.it/trasparenza/sites/default/files/Bando_7-2026_Instructor_IELTS.pdf"

response = requests.get(pdf_url)

print("Download PDF:", response.status_code)

pdf_file = BytesIO(response.content)

reader = PdfReader(pdf_file)

print("Numero pagine:", len(reader.pages))

testo = ""

for page in reader.pages:
    testo += page.extract_text() or ""

print("\nPRIMI 3000 CARATTERI:\n")
print(testo[:3000])
