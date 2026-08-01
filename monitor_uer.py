import re
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


PAGINE_UER = [
    {
        "nome": "Docenti a contratto - Art. 23",
        "tipo": "docenza",
        "url": (
            "https://www.uer.it/ateneo/concorsi-e-bandi/"
            "bandi-per-il-reclutamento-di-docenti-a-contratto-"
            "art-23-comma-2-della-l-n-240-2010/"
        ),
    },
    {
        "nome": "Professori di I e II fascia - Art. 18",
        "tipo": "prima_fascia",
        "url": (
            "https://www.uer.it/ateneo/concorsi-e-bandi/"
            "bandi-per-il-reclutamento-di-professori-di-i-e-di-ii-"
            "fascia-art-18-della-l-n-240-2010/"
        ),
    },
    {
        "nome": "Manifestazioni di interesse - Professori I e II fascia",
        "tipo": "prima_fascia",
        "url": (
            "https://www.uer.it/ateneo/concorsi-e-bandi/"
            "procedure-selettive-per-la-raccolta-di-manifestazioni-"
            "di-interesse-per-la-chiamata-di-professori-di-i-e-di-ii-fascia/"
        ),
    },
    {
        "nome": "Procedure valutative - Art. 24, commi 5 e 6",
        "tipo": "prima_fascia",
        "url": (
            "https://www.uer.it/ateneo/concorsi-e-bandi/"
            "procedure-valutative/"
        ),
    },
]

PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore ordinario",
    "professoressa ordinaria",
    "professore di ruolo di prima fascia",
    "professoressa di ruolo di prima fascia",
]

PAROLE_SECONDA_FASCIA = [
    "seconda fascia",
    "ii fascia",
    "professore associato",
    "professoressa associata",
]

PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "professori a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento degli insegnamenti a contratto",
    "conferimento di insegnamenti a contratto",
    "insegnamenti a contratto",
    "incarico didattico",
    "incarichi didattici",
    "didattica integrativa",
]

PAROLE_AREA = [
    "meds-",
    "medf-",
    "bios-",
    "mvet-",
    "iinf-",
    "phys-",
    "ibio-",
    "bio/",
    "med/",
    "vet/",
    "fis/",
    "ing-inf/",
    "psic-",
    "m-psi/",
    "medicina e chirurgia",
    "medicina",
    "chirurgia",
    "psicologia",
    "scienze e tecniche psicologiche",
    "neuroscienze",
    "anatomia",
    "patologia",
    "biologia",
    "biotecnologie",
    "bioinformatica",
    "informatica",
    "laboratorio",
]

PAROLE_ACCESSORIE = [
    "commissione",
    "nomina della commissione",
    "criteri di valutazione",
    "approvazione atti",
    "approvazione degli atti",
    "verbale",
    "graduatoria",
    "esito",
    "prima riunione",
    "seconda riunione",
    "rettifica",
    "revoca",
    "rinuncia",
    "allegato",
    "domanda di partecipazione",
    "modello cv",
]

MESI = (
    "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
    "settembre|ottobre|novembre|dicembre"
)


def crea_sessione():
    sessione = requests.Session()
    sessione.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        }
    )
    return sessione


def scarica_pagina(sessione, url):
    risposta = sessione.get(url, timeout=60)
    print("Status code:", risposta.status_code)
    print("URL finale:", risposta.url)
    print("Dimensione HTML:", len(risposta.text))
    risposta.raise_for_status()
    return risposta.text


def normalizza_testo(testo):
    if testo is None:
        return ""
    return " ".join(unescape(str(testo)).split())


def normalizza_link(base_url, href):
    link = urljoin(base_url, href)
    parti = urlsplit(link)
    return urlunsplit((parti.scheme, parti.netloc, parti.path, parti.query, ""))


def contiene(testo, parole):
    testo_lower = testo.lower()
    return any(parola in testo_lower for parola in parole)


def pulisci_pagina(soup):
    for selettore in [
        "script", "style", "header", "footer", "nav", "aside", "form",
        ".menu", ".navbar", ".breadcrumb", ".breadcrumbs", ".sidebar",
        ".site-header", ".site-footer", "[role='navigation']",
    ]:
        for elemento in soup.select(selettore):
            elemento.decompose()


def trova_contenuto(soup):
    for selettore in [
        "main", "article", "#content", "#main-content", ".entry-content",
        ".page-content", ".content-area", "[role='main']",
    ]:
        elemento = soup.select_one(selettore)
        if elemento is not None:
            testo = normalizza_testo(elemento.get_text(" ", strip=True))
            if len(testo) >= 50:
                return elemento
    return soup.body or soup


def e_documento(link):
    link_lower = link.lower()
    return any(estensione in link_lower for estensione in [
        ".pdf", ".doc", ".docx", ".odt",
    ])


def testo_locale(elemento):
    for nodo in elemento.parents:
        if not isinstance(nodo, Tag):
            continue
        if nodo.name in ["li", "p", "section", "article", "div"]:
            testo = normalizza_testo(nodo.get_text(" ", strip=True))
            if 25 <= len(testo) <= 3500:
                return testo
        if nodo.name == "main":
            break

    precedenti = []
    for vicino in elemento.previous_elements:
        if len(precedenti) >= 14:
            break
        if isinstance(vicino, NavigableString):
            testo = normalizza_testo(vicino)
            if testo:
                precedenti.append(testo)
    precedenti.reverse()

    successivi = []
    for vicino in elemento.next_elements:
        if len(successivi) >= 18:
            break
        if isinstance(vicino, NavigableString):
            testo = normalizza_testo(vicino)
            if testo:
                successivi.append(testo)

    return normalizza_testo(" ".join(precedenti + successivi))[:3500]


def estrai_scadenze(testo):
    risultati = []
    patterns = [
        re.compile(
            r"scadenza(?:\s+bando)?\s*(?:il|:)?\s*"
            r"(\d{1,2}[/.]\d{1,2}[/.]\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"scadenza(?:\s+bando)?\s*(?:il|:)?\s*"
            r"(\d{1,2}\s+(?:" + MESI + r")\s+\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"entro\s+(?:e\s+non\s+oltre\s+)?(?:il\s+)?"
            r"(\d{1,2}\s+(?:" + MESI + r")\s+\d{4})",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        for risultato in pattern.findall(testo):
            risultato = normalizza_testo(risultato)
            if risultato not in risultati:
                risultati.append(risultato)
    return risultati


def candidato_utile(tipo, titolo, contesto, link):
    testo = normalizza_testo(f"{titolo} {contesto} {link}")

    if contiene(titolo, PAROLE_ACCESSORIE):
        return False

    if tipo == "docenza":
        return contiene(testo, PAROLE_DOCENZA)

    if tipo == "prima_fascia":
        return (
            contiene(testo, PAROLE_PRIMA_FASCIA)
            and not contiene(testo, PAROLE_SECONDA_FASCIA)
        )

    return False


def analizza_pagina(pagina, html):
    soup = BeautifulSoup(html, "html.parser")
    pulisci_pagina(soup)
    contenuto = trova_contenuto(soup)

    risultati = []
    links_visti = set()

    for elemento in contenuto.find_all("a", href=True):
        href = elemento.get("href", "")
        link = normalizza_link(pagina["url"], href)
        if link in links_visti:
            continue

        titolo = normalizza_testo(elemento.get_text(" ", strip=True))
        if not titolo:
            continue

        contesto = testo_locale(elemento)
        if not candidato_utile(pagina["tipo"], titolo, contesto, link):
            continue

        testo_completo = normalizza_testo(f"{titolo} {contesto} {link}")
        links_visti.add(link)
        risultati.append(
            {
                "titolo": titolo,
                "link": link,
                "documento": e_documento(link),
                "prima_fascia": contiene(testo_completo, PAROLE_PRIMA_FASCIA),
                "docenza": contiene(testo_completo, PAROLE_DOCENZA),
                "area": contiene(testo_completo, PAROLE_AREA),
                "seconda_fascia": contiene(
                    testo_completo, PAROLE_SECONDA_FASCIA
                ),
                "scadenze": estrai_scadenze(testo_completo),
                "contesto": contesto,
            }
        )

    print("\n========================================")
    print("SEZIONE:", pagina["nome"])
    print("TIPO:", pagina["tipo"])
    print("========================================")
    print("CANDIDATI PERTINENTI TROVATI:", len(risultati))

    for numero, risultato in enumerate(risultati, start=1):
        print("\n----------------------------------------")
        print("RISULTATO:", numero)
        print("TITOLO:", risultato["titolo"])
        print("DOCUMENTO:", risultato["documento"])
        print("PRIMA FASCIA:", risultato["prima_fascia"])
        print("SECONDA FASCIA:", risultato["seconda_fascia"])
        print("DOCENZA:", risultato["docenza"])
        print("AREA INTERESSE:", risultato["area"])
        print("SCADENZE:", risultato["scadenze"])
        print("LINK:", risultato["link"])
        print("CONTESTO:", risultato["contesto"][:1800])

    return risultati


print("\n=== DIAGNOSTICA UNIVERSITA EUROPEA DI ROMA ===\n")

sessione = crea_sessione()
totale = 0

for pagina in PAGINE_UER:
    print("\nControllo:", pagina["nome"])
    try:
        html = scarica_pagina(sessione, pagina["url"])
        risultati = analizza_pagina(pagina, html)
        totale += len(risultati)
    except Exception as errore:
        print("ERRORE NELLA SEZIONE:", pagina["nome"])
        print(str(errore))

print("\nTOTALE CANDIDATI PERTINENTI:", totale)
print("\n=== FINE DIAGNOSTICA UER ===")

