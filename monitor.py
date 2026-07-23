import json
import requests

from io import BytesIO
from pypdf import PdfReader

from datetime import datetime
from bs4 import BeautifulSoup


# =====================================
# CONFIGURAZIONE
# =====================================

STORICO_FILE = "storico.json"

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
    "giurisprudenza",
    "ielts",
    "lingua inglese",
    "branding",
    "moda",
    "archeologia",
    "terapia occupazionale"
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
# PRIORITA'
# =====================================

def assegna_priorita(testo):

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


# =====================================
# PDF
# =====================================

def leggi_pdf(pdf_url):

    try:

        response = requests.get(
            pdf_url,
            timeout=60
        )

        reader = PdfReader(
            BytesIO(response.content)
        )

        testo = ""

        for pagina in reader.pages:

            testo += (
                pagina.extract_text() or ""
            )

        return testo.lower()

    except Exception:

        return ""


# =====================================
# RICERCA URL PDF
# =====================================

def trova_pdf(dettaglio_html):

    pdf_urls = []

    import re

    pattern = (
        r'https://web\.uniroma1\.it'
        r'/trasparenza/sites/default/files/'
        r'[^"\s<>]+\.pdf'
    )

    trovati = re.findall(
        pattern,
        dettaglio_html
    )

    for url in trovati:

        if url not in pdf_urls:

            pdf_urls.append(url)

    return pdf_urls


# =====================================
# SAPIENZA
# =====================================

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

        if (
            "/trasparenza/dettaglio_bando_albo/"
            not in href
        ):
            continue

        dettaglio_url = (
            "https://web.uniroma1.it" + href
        )

        try:

            dettaglio = requests.get(
                dettaglio_url,
                timeout=30
            )

            dettagli_html = dettaglio.text

            dettaglio_soup = BeautifulSoup(
                dettagli_html,
                "html.parser"
            )

            testo_dettaglio = (
                dettaglio_soup.get_text("\n")
            )

            righe = [
                r.strip()
                for r in testo_dettaglio.splitlines()
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

            pdf_urls = trova_pdf(
                dettagli_html
            )

            testo_completo = (
                testo_dettaglio.lower()
            )

            for pdf_url in pdf_urls:

                testo_pdf = leggi_pdf(
                    pdf_url
                )

                testo_completo += (
                    "\n" + testo_pdf
                )

            priorita, keyword = (
                assegna_priorita(
                    testo_completo
                )
            )

            if not priorita:
                continue

            risultati.append(
                {
                    "id": href.split("/")[-1],
                    "priorita": priorita,
                    "keyword": keyword,
                    "titolo": titolo,
                    "scadenza": data_scadenza,
                    "url": dettaglio_url
                }
            )

        except Exception as e:

            print(
                "Errore:",
                titolo,
                str(e)
            )

    return risultati


# =====================================
# MAIN
# =====================================

print("\n=== MONITOR DOCENZE ===\n")

storico = carica_storico()

gia_segnalati = set(
    storico["bandi_gia_segnalati"]
)

bandi = cerca_bandi_sapienza()

nuovi = []

for bando in bandi:

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

    for b in nuovi:

        print(
            f"[{b['priorita']}]"
        )
        print(
            b["titolo"]
        )
        print(
            "Keyword:",
            b["keyword"]
        )
        print(
            "Scadenza:",
            b["scadenza"]
        )
        print(
            "URL:",
            b["url"]
        )
        print()

print("=== FINE ===")
