import requests
from bs4 import BeautifulSoup
from datetime import datetime

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
    "lingua",
    "ielts"
]

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

strongs = soup.find_all("strong")

oggi = datetime.now()

print("\n=== BANDI NON SCADUTI E PERTINENTI ===\n")

for i in range(len(strongs)):

    titolo = strongs[i].get_text(" ", strip=True)

    if titolo in [
        "",
        "Data pubblicazione bando:",
        "Data scadenza bando:",
        "codice bando:",
        "Filtra",
        "Bandi di concorso pubblicati antecedentemente all'8 febbraio 2016"
    ]:
        continue

    try:

        data_scadenza = strongs[i + 3].parent.get_text(
            " ",
            strip=True
        ).replace(
            "Data scadenza bando:",
            ""
        ).strip()

        data_scadenza_dt = datetime.strptime(
            data_scadenza,
            "%d-%m-%Y"
        )

        if data_scadenza_dt < oggi:
            continue

        titolo_lower = titolo.lower()

        escluso = False

        for parola in ESCLUSIONI:
            if parola in titolo_lower:
                escluso = True

        if escluso:
            continue

        priorita = None

        for parola in PRIORITA_ALTA:
            if parola in titolo_lower:
                priorita = "ALTA"

        if priorita is None:
            for parola in PRIORITA_MEDIA:
                if parola in titolo_lower:
                    priorita = "MEDIA"

        if priorita is None:
            for parola in PRIORITA_BASSA:
                if parola in titolo_lower:
                    priorita = "BASSA"

        if priorita:

            print(f"[{priorita}]")
            print(titolo)
            print("Scadenza:", data_scadenza)
            print()

    except Exception:
        pass
