import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL_SAPIENZA = (
    "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
    "?field_user_centro_spesa_ugov_tid=All"
    "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
    "&field_bis_sc_e_ssd_tid=All"
    "&keys="
    "&field_bis_gsd_ssd_target_id=All"
)

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
    "tecniche di laboratorio biomedico",
    "laboratorio biomedico"
]

PRIORITA_BASSA = [
    "reumatologia",
    "fisiologia",
    "istologia"
]

ESCLUSIONI = [
    "economia",
    "ielts",
    "lingua inglese",
    "branding",
    "moda",
    "archeologia",
    "storia dell'arte",
    "diritto",
    "giurisprudenza",
    "letteratura",
    "terapia occupazionale"
]

oggi = datetime.now()

print("\n=== MONITOR SAPIENZA ===\n")

response = requests.get(URL_SAPIENZA, timeout=30)

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

bandi_trovati = []

for link in soup.find_all("a"):

    titolo = link.get_text(" ", strip=True)
    href = link.get("href")

    if not href:
        continue

    if "/trasparenza/dettaglio_bando_albo/" not in href:
        continue

    dettaglio_url = "https://web.uniroma1.it" + href

    try:

        dettaglio = requests.get(
            dettaglio_url,
            timeout=30
        )

        dettaglio_soup = BeautifulSoup(
            dettaglio.text,
            "html.parser"
        )

        testo = dettaglio_soup.get_text("\n")

        righe = [
            r.strip()
            for r in testo.splitlines()
            if r.strip()
        ]

        data_scadenza = None

        for i, riga in enumerate(righe):

            if riga == "Data scadenza:" and i + 1 < len(righe):
                data_scadenza = righe[i + 1]
                break

        if not data_scadenza:
            continue

        try:

            data_dt = datetime.strptime(
                data_scadenza,
                "%d-%m-%Y"
            )

        except Exception:
            continue

        if data_dt < oggi:
            continue

        testo_lower = testo.lower()

        escluso = False

        for parola in ESCLUSIONI:

            if parola in testo_lower:
                escluso = True
                break

        if escluso:
            continue

        priorita = None
        keyword = None

        for parola in PRIORITA_ALTA:

            if parola in testo_lower:
                priorita = "ALTA"
                keyword = parola
                break

        if priorita is None:

            for parola in PRIORITA_MEDIA:

                if parola in testo_lower:
                    priorita = "MEDIA"
                    keyword = parola
                    break

        if priorita is None:

            for parola in PRIORITA_BASSA:

                if parola in testo_lower:
                    priorita = "BASSA"
                    keyword = parola
                    break

        if priorita:

            bandi_trovati.append(
                {
                    "priorita": priorita,
                    "titolo": titolo,
                    "scadenza": data_scadenza,
                    "keyword": keyword,
                    "url": dettaglio_url
                }
            )

    except Exception:
        pass


ordine = {
    "ALTA": 1,
    "MEDIA": 2,
    "BASSA": 3
}

bandi_trovati.sort(
    key=lambda x: ordine[x["priorita"]]
)

if not bandi_trovati:

    print("NESSUN BANDO PERTINENTE TROVATO")

else:

    print(
        f"Totale bandi pertinenti: {len(bandi_trovati)}\n"
    )

    for bando in bandi_trovati:

        print(
            f"[{bando['priorita']}]"
        )

        print(
            "Titolo:",
            bando["titolo"]
        )

        print(
            "Scadenza:",
            bando["scadenza"]
        )

        print(
            "Keyword:",
            bando["keyword"]
        )

        print(
            "URL:",
            bando["url"]
        )

        print()

print("=== FINE ===")
