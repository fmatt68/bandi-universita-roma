import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================
# CONFIGURAZIONE
# ==========================

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
    "giurisprudenza",
    "ielts",
    "lingua inglese",
    "branding",
    "moda",
    "archeologia",
    "terapia occupazionale"
]


# ==========================
# FUNZIONI
# ==========================

def determina_priorita(testo):

    testo = testo.lower()

    for parola in ESCLUSIONI:
        if parola in testo:
            return None, None

    for parola in PRIORITA_ALTA:
        if parola in testo:
            return "ALTA", parola

    for parola in PRIORITA_MEDIA:
        if parola in testo:
            return "MEDIA", parola

    for parola in PRIORITA_BASSA:
        if parola in testo:
            return "BASSA", parola

    return None, None


def estrai_data_scadenza(testo):

    righe = [
        r.strip()
        for r in testo.splitlines()
        if r.strip()
    ]

    for i, riga in enumerate(righe):

        if riga == "Data scadenza:" and i + 1 < len(righe):

            try:
                return datetime.strptime(
                    righe[i + 1],
                    "%d-%m-%Y"
                )
            except:
                return None

    return None


def cerca_bandi_sapienza():

    risultati = []

    url = (
        "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
        "?field_user_centro_spesa_ugov_tid=All"
        "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
        "&field_bis_sc_e_ssd_tid=All"
        "&keys="
        "&field_bis_gsd_ssd_target_id=All"
    )

    pagina = requests.get(url, timeout=30)

    soup = BeautifulSoup(
        pagina.text,
        "html.parser"
    )

    oggi = datetime.now()

    for link in soup.find_all("a"):

        href = link.get("href")
        titolo = link.get_text(" ", strip=True)

        if not href:
            continue

        if "/trasparenza/dettaglio_bando_albo/" not in href:
            continue

        dettaglio_url = (
            "https://web.uniroma1.it" + href
        )

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

            data_scadenza = estrai_data_scadenza(
                testo
            )

            if not data_scadenza:
                continue

            if data_scadenza < oggi:
                continue

            priorita, keyword = determina_priorita(
                testo
            )

            if not priorita:
                continue

            risultati.append(
                {
                    "titolo": titolo,
                    "priorita": priorita,
                    "keyword": keyword,
                    "scadenza": data_scadenza.strftime(
                        "%d-%m-%Y"
                    ),
                    "url": dettaglio_url
                }
            )

        except Exception:
            continue

    return risultati


# ==========================
# MAIN
# ==========================

print("\n=== MONITOR SAPIENZA ===\n")

bandi = cerca_bandi_sapienza()

ordine = {
    "ALTA": 1,
    "MEDIA": 2,
    "BASSA": 3
}

bandi.sort(
    key=lambda x: ordine[x["priorita"]]
)

if not bandi:

    print(
        "NESSUN BANDO PERTINENTE TROVATO"
    )

else:

    print(
        f"Trovati {len(bandi)} bandi pertinenti\n"
    )

    for bando in bandi:

        print(
            f"[{bando['priorita']}]"
        )

        print(
            "Titolo:",
            bando["titolo"]
        )

        print(
            "Keyword:",
            bando["keyword"]
        )

        print(
            "Scadenza:",
            bando["scadenza"]
        )

        print(
            "URL:",
            bando["url"]
        )

        print()

print("=== FINE ===")
