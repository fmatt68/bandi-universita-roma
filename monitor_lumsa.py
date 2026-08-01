import re
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


PAGINE_LUMSA = [
    {
        "nome": "Docenze a contratto - Albo degli idonei",
        "tipo": "docenza",
        "url": "https://lumsa.it/it/docenze-a-contratto-albo-degli-idonei",
    },
    {
        "nome": "Tutti i bandi e le opportunita",
        "tipo": "generale",
        "url": "https://lumsa.it/it/tutti-i-bandi",
    },
]

PAROLE_DOCENZA = [
    "docente a contratto", "docenti a contratto", "docenza a contratto",
    "docenze a contratto", "professore a contratto", "professoressa a contratto",
    "incarico di insegnamento", "incarichi di insegnamento",
    "conferimento di incarichi di insegnamento", "albo degli idonei",
    "manifestazione di interesse", "idoneita", "idoneità",
]

PAROLE_PRIMA_FASCIA = [
    "prima fascia", "i fascia", "professore ordinario",
    "professoressa ordinaria", "professore di ruolo di prima fascia",
]

PAROLE_AREA = [
    "meds-", "medf-", "bios-", "iinf-", "phys-", "psic-", "m-psi/",
    "bio/", "med/", "fis/", "ing-inf/", "medicina", "psicologia",
    "neuroscienze", "biologia", "biotecnologie", "bioinformatica",
    "informatica", "scienze della formazione", "laboratorio",
]

PAROLE_ACCESSORIE = [
    "assegnazione", "graduatoria", "esito", "commissione", "verbale",
    "approvazione atti", "regolamento", "tabella compensi", "allegato",
    "modello", "domanda",
]

MESI = (
    "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
    "settembre|ottobre|novembre|dicembre"
)


def crea_sessione():
    sessione = requests.Session()
    sessione.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    })
    return sessione


def normalizza_testo(testo):
    if testo is None:
        return ""
    return " ".join(unescape(str(testo)).split())


def normalizza_link(base, href):
    link = urljoin(base, href)
    parti = urlsplit(link)
    return urlunsplit((parti.scheme, parti.netloc, parti.path, parti.query, ""))


def contiene(testo, parole):
    testo = testo.lower()
    return any(parola in testo for parola in parole)


def scarica(sessione, url):
    risposta = sessione.get(url, timeout=60)
    print("Status code:", risposta.status_code)
    print("URL finale:", risposta.url)
    print("Dimensione HTML:", len(risposta.text))
    risposta.raise_for_status()
    return risposta.text


def pulisci(soup):
    for selettore in [
        "script", "style", "header", "footer", "nav", "aside", "form",
        ".menu", ".navbar", ".breadcrumb", ".sidebar", "[role='navigation']",
    ]:
        for elemento in soup.select(selettore):
            elemento.decompose()


def contenuto_principale(soup):
    for selettore in [
        "main", "article", "#content", "#main-content", ".page-content",
        ".entry-content", ".content-area", "[role='main']",
    ]:
        elemento = soup.select_one(selettore)
        if elemento is not None and len(normalizza_testo(elemento.get_text(" ", strip=True))) >= 50:
            return elemento
    return soup.body or soup


def estrai_scadenze(testo):
    risultati = []
    patterns = [
        re.compile(
            r"scadenza(?:\s+presentazione\s+domande)?\s*:?\s*"
            r"(\d{1,2}[/.]\d{1,2}[/.]\d{4})", re.I
        ),
        re.compile(
            r"scadenza(?:\s+presentazione\s+domande)?\s*:?\s*"
            r"(\d{1,2}\s+(?:" + MESI + r")\s+\d{4})", re.I
        ),
        re.compile(
            r"entro\s+(?:e\s+non\s+oltre\s+)?(?:il\s+)?"
            r"(\d{1,2}\s+(?:" + MESI + r")\s+\d{4})", re.I
        ),
    ]
    for pattern in patterns:
        for valore in pattern.findall(testo):
            valore = normalizza_testo(valore)
            if valore not in risultati:
                risultati.append(valore)
    return risultati


def contesto_locale(elemento):
    for nodo in elemento.parents:
        if nodo.name in ["li", "p", "section", "article", "div"]:
            testo = normalizza_testo(nodo.get_text(" ", strip=True))
            if 25 <= len(testo) <= 3500:
                return testo
        if nodo.name == "main":
            break
    return normalizza_testo(elemento.parent.get_text(" ", strip=True))[:3500]


def analizza(pagina, html):
    soup = BeautifulSoup(html, "html.parser")
    pulisci(soup)
    contenuto = contenuto_principale(soup)
    risultati = []
    visti = set()

    for a in contenuto.find_all("a", href=True):
        titolo = normalizza_testo(a.get_text(" ", strip=True))
        link = normalizza_link(pagina["url"], a.get("href", ""))
        if not titolo or link in visti:
            continue

        contesto = contesto_locale(a)
        testo = normalizza_testo(f"{titolo} {contesto} {link}")

        if contiene(titolo, PAROLE_ACCESSORIE):
            continue

        docenza = contiene(testo, PAROLE_DOCENZA)
        prima_fascia = contiene(testo, PAROLE_PRIMA_FASCIA)
        area = contiene(testo, PAROLE_AREA)

        if not (docenza or prima_fascia):
            continue

        visti.add(link)
        risultati.append({
            "titolo": titolo,
            "link": link,
            "docenza": docenza,
            "prima_fascia": prima_fascia,
            "area": area,
            "scadenze": estrai_scadenze(testo),
            "contesto": contesto,
        })

    print("\n========================================")
    print("SEZIONE:", pagina["nome"])
    print("========================================")
    print("CANDIDATI TROVATI:", len(risultati))

    for numero, risultato in enumerate(risultati, 1):
        print("\n----------------------------------------")
        print("RISULTATO:", numero)
        print("TITOLO:", risultato["titolo"])
        print("DOCENZA:", risultato["docenza"])
        print("PRIMA FASCIA:", risultato["prima_fascia"])
        print("AREA INTERESSE:", risultato["area"])
        print("SCADENZE:", risultato["scadenze"])
        print("LINK:", risultato["link"])
        print("CONTESTO:", risultato["contesto"][:1800])

    return risultati


print("\n=== DIAGNOSTICA LUMSA ===\n")
sessione = crea_sessione()
totale = 0

for pagina in PAGINE_LUMSA:
    print("\nControllo:", pagina["nome"])
    try:
        html = scarica(sessione, pagina["url"])
        totale += len(analizza(pagina, html))
    except Exception as errore:
        print("ERRORE NELLA SEZIONE:", pagina["nome"])
        print(str(errore))

print("\nTOTALE CANDIDATI:", totale)
print("\n=== FINE DIAGNOSTICA LUMSA ===")
