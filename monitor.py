import json
import requests
import re

from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from pypdf import PdfReader


# =====================================
# CONFIG
# =====================================

URL_SAPIENZA = (
    "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
    "?field_user_centro_spesa_ugov_tid=All"
    "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
    "&field_bis_sc_e_ssd_tid=All"
    "&keys="
    "&field_bis_gsd_ssd_target_id=All"
)

STORICO_FILE = "storico.json"

PRIORITA_ALTA = [
    "biologia",
    "biologia molecolare",
    "biologia cellulare",
    "scienze biologiche",
    "biotecnologie",
    "genetica",
    "genetica medica",
    "immunologia",
    "oncologia",
    "ematologia"
]

PRIORITA_MEDIA = [
    "biochimica",
    "patologia generale",
    "medicina di laboratorio",
    "laboratorio biomedico",
    "tecniche di laboratorio biomedico"
]

PRIORITA_BASSA = [
    "fisiologia",
    "istologia",
    "reumatologia"
]


# =====================================
# STORICO
# =====================================

def carica_storico():

    try:

        with open(
            STORICO_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "bandi_gia_segnalati": []
        }


def salva_storico(storico):

    with open(
        STORICO_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            storico,
            f,
            indent=2,
            ensure_ascii=False
        )


# =====================================
# PDF
# =====================================

def trova_pdf_url(html):

    pdf_urls = []

    matches = re.findall(
        r'https://web\.uniroma1\.it/trasparenza/sites/default/files/[^\s"<>\']+\.pdf',
        html,
        flags=re.IGNORECASE
    )

    for url in matches:

        if url not in pdf_urls:
            pdf_urls.append(url)

    return pdf_urls


def leggi_pdf(url):

    try:

        response = requests.get(
            url,
            timeout=60
        )

        if response.status_code != 200:
            return ""

        reader = PdfReader(
            BytesIO(response.content)
        )

        testo = ""

        for pagina in reader.pages:

            testo += (
                pagina.extract_text()
                or ""
            )

        return testo.lower()

    except Exception:

        return ""


# =====================================
# PRIORITA
# =====================================

def classifica(testo):

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


# =====================================
# MAIN
# =====================================

print("\n=== MONITOR DOCENZE ===\n")

storico = carica_storico()

gia_segnalati = set(
    storico["bandi_gia_segnalati"]
)

oggi = datetime.now()

pagina = requests.get(
    URL_SAPIENZA,
    timeout=30
)

soup = BeautifulSoup(
    pagina.text,
    "html.parser"
)

nuovi_bandi = []

for link in soup.find_all("a"):

    href = link.get("href")
    titolo = link.get_text(
        " ",
        strip=True
    )

    if not href:
        continue

    if "/trasparenza/dettaglio_bando_albo/" not in href:
        continue

    bando_id = href.split("/")[-1]

    if bando_id in gia_segnalati:
        continue

    dettaglio_url = (
        "https://web.uniroma1.it" + href
    )

    try:

        dettaglio = requests.get(
            dettaglio_url,
            timeout=30
        )

        html = dettaglio.text

        dettaglio_soup = BeautifulSoup(
            html,
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

            if (
                riga == "Data scadenza:"
                and i + 1 < len(righe)
            ):
                data_scadenza = (
                    righe[i + 1]
                )
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

        pdf_urls = trova_pdf_url(html)

        testo_completo = ""

        for pdf_url in pdf_urls:

            testo_completo += (
                leggi_pdf(pdf_url)
                + "\n"
            )

        priorita, keyword = classifica(
            testo_completo
        )

        if not priorita:
            continue

        nuovi_bandi.append(
            {
                "id": bando_id,
                "titolo": titolo,
                "scadenza": data_scadenza,
                "priorita": priorita,
                "keyword": keyword,
                "url": dettaglio_url
            }
        )

    except Exception as e:

        print(
            "ERRORE:",
            titolo
        )

        print(str(e))

ordine = {
    "ALTA": 1,
    "MEDIA": 2,
    "BASSA": 3
}

nuovi_bandi.sort(
    key=lambda x: ordine[x["priorita"]]
)

if not nuovi_bandi:

    print(
        "NESSUN NUOVO BANDO PERTINENTE"
    )

else:

    print(
        f"NUOVI BANDI TROVATI: {len(nuovi_bandi)}\n"
    )

    for bando in nuovi_bandi:

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

        storico[
            "bandi_gia_segnalati"
        ].append(
            bando["id"]
        )

salva_storico(storico)

print("\n=== FINE ===")
