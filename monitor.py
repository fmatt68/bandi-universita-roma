import requests
from bs4 import BeautifulSoup

PRIORITA_ALTA = [
    "ematologia",
    "oncologia",
    "immunologia",
    "genetica",
    "genetica medica",
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

ESCLUSIONI = [
    "infermieristica",
    "fisioterapia",
    "terapia occupazionale",
    "ostetricia",
    "tecniche radiologiche",
    "giurisprudenza",
    "economia",
    "ingegneria",
    "psicologia"
]

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

testo = soup.get_text("\n")

righe = testo.splitlines()

print("\n=== BANDI POTENZIALMENTE INTERESSANTI ===\n")

for riga in righe:

    riga = riga.strip()

    if len(riga) < 20:
        continue

    testo_lower = riga.lower()

    escluso = False

    for parola in ESCLUSIONI:
        if parola in testo_lower:
            escluso = True

    if escluso:
        continue

    priorita = None

    for parola in PRIORITA_ALTA:
        if parola in testo_lower:
            priorita = "ALTA"

    if priorita is None:
        for parola in PRIORITA_MEDIA:
            if parola in testo_lower:
                priorita = "MEDIA"

    if priorita is None:
        for parola in PRIORITA_BASSA:
            if parola in testo_lower:
                priorita = "BASSA"

    if priorita:
        print(f"[{priorita}] {riga}")
