import json
import re
import requests

from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from pypdf import PdfReader


# ==========================================
# CONFIG
# ==========================================

STORICO_FILE = "storico.json"

URL_SAPIENZA = (
    "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66"
    "?field_user_centro_spesa_ugov_tid=All"
    "&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D="
    "&field_bis_sc_e_ssd_tid=All"
    "&keys="
    "&field_bis_gsd_ssd_target_id=All"
)

KEYWORDS_ALTA = [
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

KEYWORDS_MEDIA = [
    "biochimica",
    "patologia generale",
    "medicina di laboratorio",
    "laboratorio biomedico",
    "tecniche di laboratorio biomedico"
]

KEYWORDS_BASSA = [
    "fisiologia",
    "istologia",
    "reumatologia"
]

FILTRO_TITOLO = [
    "health",
    "sanitario",
    "medicina",
    "medico",
    "biologia",
    "biotecnologie",
    "genetica",
    "oncologia",
    "ematologia",
    "farmacia",
    "farmacologia",
    "biomedico",
    "laboratorio",
    "patologia",
    "immunologia"
]


# ==========================================
# STORICO
# ==========================================

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


# ==========================================
# PDF
# ==========================================

def trova_pdf_url(html):

    matches = re.findall(
        r'https://web\.uniroma1\.it/trasparenza/sites/default/files/[^\s"<>\']+\.pdf',
        html,
        flags=re.IGNORECASE
    )

    risultati = []

    for url in matches:

        if url not in risultati:
            risultati.append(url)

    return risultati


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


# ==========================================
# CLASSIFICAZIONE
# ==========================================

def classifica(testo):

    testo = testo.lower()

    for parola in KEYWORDS_ALTA:

        if parola in testo:
            return "ALTA", parola

    for parola in KEYWORDS_MEDIA:

        if parola in testo:
            return "MEDIA", parola

    for parola in KEYWORDS_BASSA:

        if parola in testo:
            return "BASSA", parola

    return None, None


# ==========================================
# SAPIENZA
# ==========================================

def cerca_bandi_sapienza():

    risultati = []

    oggi = datetime.now()

    pagina = requests.get(
        URL_SAPIENZA,
        timeout=30
    )

    soup = BeautifulSoup(
        pagina.text,
        "html.parser"
    )

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

            testo = dettaglio_soup.get_text(
                "\n"
            )

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

            titolo_lower = titolo.lower()

            candidato = False

            for parola in FILTRO_TITOLO:

                if parola in titolo_lower:
                    candidato = True
                    break

            pdf_urls = trova_pdf_url(html)

            testo_completo = ""

            for pdf_url in pdf_urls:

                print(
                    "PDF:",
                    pdf_url.split("/")[-1]
                )

                testo_completo += (
                    leggi_pdf(pdf_url)
                )

            if not candidato:

                if any(
                    x in testo_completo
                    for x in (
                        KEYWORDS_ALTA
                        + KEYWORDS_MEDIA
                        + KEYWORDS_BASSA
                    )
                ):
                    candidato = True

            if not candidato:
                continue

            priorita, keyword = classifica(
                testo_completo
            )

            if not priorita:
                continue

            risultati.append(
                {
                    "id": href.split("/")[-1],
                    "titolo": titolo,
                    "scadenza": data_scadenza,
                    "priorita": priorita,
                    "keyword": keyword,
                    "url": dettaglio_url
                }
            )

        except Exception as e:

            print("ERRORE:", titolo)
            print(str(e))

    return risultati


# ==========================================
# MAIN
# ==========================================

print("\n=== MONITOR DOCENZE V2 ===\n")

storico = carica_storico()

gia_segnalati = set(
    storico["bandi_gia_segnalati"]
)

tutti_bandi = []

tutti_bandi.extend(
    cerca_bandi_sapienza()
)

nuovi = []

for bando in tutti_bandi:

    if bando["id"] not in gia_segnalati:

        nuovi.append(bando)

        storico[
            "bandi_gia_segnalati"
        ].append(
            bando["id"]
        )

salva_storico(storico)

ordine = {
    "ALTA": 1,
    "MEDIA": 2,
    "BASSA": 3
}

nuovi.sort(
    key=lambda x: ordine[x["priorita"]]
)

if not nuovi:

    print(
        "NESSUN NUOVO BANDO PERTINENTE"
    )

else:

    print(
        f"NUOVI BANDI TROVATI: {len(nuovi)}\n"
    )

    for bando in nuovi:

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

print("\n=== FINE ===")
