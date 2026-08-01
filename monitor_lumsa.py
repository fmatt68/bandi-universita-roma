import re
from html import unescape

import requests
from bs4 import BeautifulSoup


PAGINE_LUMSA = [
    {
        "nome": "Docenze a contratto - Albo degli idonei",
        "url": "https://lumsa.it/it/docenze-a-contratto-albo-degli-idonei",
        "tipo": "docenza",
    },
    {
        "nome": "Reclutamento docenti, ricercatori e tutor",
        "url": "https://lumsa.it/it/reclutamento-docenti-ricercatori-e-tutor",
        "tipo": "reclutamento",
    },
]

PAROLE_APERTURA = [
    "manifestazione di interesse",
    "bando",
    "procedura selettiva",
    "procedura di valutazione",
    "selezione per",
    "avviso di selezione",
]

PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "docenze a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento di incarichi di insegnamento",
    "albo degli idonei",
    "idoneita all'insegnamento",
    "idoneità all’insegnamento",
]

PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore ordinario",
    "professoressa ordinaria",
    "professore di ruolo di prima fascia",
]

PAROLE_AREA = [
    "meds-",
    "medf-",
    "bios-",
    "iinf-",
    "phys-",
    "psic-",
    "m-psi/",
    "bio/",
    "med/",
    "fis/",
    "ing-inf/",
    "medicina",
    "psicologia",
    "neuroscienze",
    "biologia",
    "biotecnologie",
    "bioinformatica",
    "informatica",
    "scienze della formazione",
    "laboratorio",
]

PAROLE_DA_ESCLUDERE = [
    "assegnazioni docenze",
    "assegnazione docenza",
    "graduatoria",
    "esito",
    "commissione",
    "verbale",
    "approvazione atti",
    "regolamento",
    "tabella compensi",
    "allegato",
    "modello",
    "domanda di partecipazione",
]

MESI = (
    "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
    "settembre|ottobre|novembre|dicembre"
)


def normalizza_testo(testo):
    if testo is None:
        return ""
    return " ".join(unescape(str(testo)).split())


def contiene(testo, parole):
    testo_lower = testo.lower()
    return any(parola in testo_lower for parola in parole)


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


def scarica(sessione, url):
    risposta = sessione.get(url, timeout=60)
    print("Status code:", risposta.status_code)
    print("URL finale:", risposta.url)
    print("Dimensione HTML:", len(risposta.text))
    risposta.raise_for_status()
    return risposta.text


def pulisci_pagina(soup):
    selettori = [
        "script",
        "style",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        ".menu",
        ".navbar",
        ".breadcrumb",
        ".breadcrumbs",
        ".sidebar",
        ".site-header",
        ".site-footer",
        "[role='navigation']",
    ]
    for selettore in selettori:
        for elemento in soup.select(selettore):
            elemento.decompose()


def trova_contenuto_principale(soup):
    selettori = [
        "main",
        "article",
        "#content",
        "#main-content",
        ".page-content",
        ".entry-content",
        ".content-area",
        "[role='main']",
    ]
    for selettore in selettori:
        elemento = soup.select_one(selettore)
        if elemento is None:
            continue
        testo = normalizza_testo(elemento.get_text(" ", strip=True))
        if len(testo) >= 100:
            return elemento
    return soup.body or soup


def estrai_righe(contenuto):
    righe = []
    testo = contenuto.get_text("\n", strip=True)
    for riga in testo.splitlines():
        riga = normalizza_testo(riga)
        if not riga:
            continue
        if righe and riga == righe[-1]:
            continue
        righe.append(riga)
    return righe


def inizia_blocco(riga):

    riga_lower = riga.lower()

    return any(
        parola in riga_lower
        for parola in PAROLE_APERTURA
    )


def crea_blocchi(righe):

    blocchi = []

    indici_inizio = []

    for indice, riga in enumerate(
        righe
    ):

        if inizia_blocco(
            riga
        ):

            indici_inizio.append(
                indice
            )

    for posizione, indice_inizio in enumerate(
        indici_inizio
    ):

        if posizione + 1 < len(
            indici_inizio
        ):

            indice_fine = indici_inizio[
                posizione + 1
            ]

        else:

            indice_fine = min(
                len(righe),
                indice_inizio + 30
            )

        righe_blocco = righe[
            indice_inizio:indice_fine
        ]

        testo_blocco = normalizza_testo(
            " ".join(
                righe_blocco
            )
        )

        if testo_blocco:

            blocchi.append(
                testo_blocco
            )

    return blocchi

def estrai_scadenze(testo):
    risultati = []
    patterns = [
        re.compile(
            r"scadenza(?:\s+presentazione\s+domande)?\s*:?\s*"
            r"(\d{1,2}[/.]\d{1,2}[/.]\d{4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"scadenza(?:\s+presentazione\s+domande)?\s*:?\s*"
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


def titolo_blocco(blocco):
    for separatore in [" Scadenza", " scadenza", " SCADENZA"]:
        if separatore in blocco:
            return blocco.split(separatore, 1)[0][:600].strip()
    return blocco[:600].strip()


def analizza_pagina(pagina, html):
    soup = BeautifulSoup(html, "html.parser")
    pulisci_pagina(soup)
    contenuto = trova_contenuto_principale(soup)
    righe = estrai_righe(contenuto)
        print(
        "\nRIGHE CON PAROLE CHIAVE:"
    )

    for riga in righe:

        if (
            contiene(
                riga,
                PAROLE_APERTURA
            )
            or contiene(
                riga,
                PAROLE_DOCENZA
            )
            or "scadenza" in riga.lower()
        ):

            print(
                "-",
                riga[:1000]
            )
    blocchi = crea_blocchi(righe)

    print("RIGHE CONTENUTO:", len(righe))
    print("BLOCCHI CANDIDATI:", len(blocchi))

    risultati = []

    for blocco in blocchi:
        titolo = titolo_blocco(blocco)

        if contiene(blocco, PAROLE_DA_ESCLUDERE):
            continue

        docenza = contiene(blocco, PAROLE_DOCENZA)
        prima_fascia = contiene(blocco, PAROLE_PRIMA_FASCIA)
        area = contiene(blocco, PAROLE_AREA)

        if not (docenza or prima_fascia):
            continue

        risultati.append(
            {
                "titolo": titolo,
                "docenza": docenza,
                "prima_fascia": prima_fascia,
                "area": area,
                "scadenze": estrai_scadenze(blocco),
                "testo": blocco,
                "pagina": pagina["url"],
            }
        )

    print("CANDIDATI PERTINENTI:", len(risultati))

    for numero, risultato in enumerate(risultati, start=1):
        print("\n----------------------------------------")
        print("RISULTATO:", numero)
        print("TITOLO:", risultato["titolo"])
        print("DOCENZA:", risultato["docenza"])
        print("PRIMA FASCIA:", risultato["prima_fascia"])
        print("AREA INTERESSE:", risultato["area"])
        print("SCADENZE:", risultato["scadenze"])
        print("PAGINA:", risultato["pagina"])
        print("TESTO:", risultato["testo"][:2000])

    return risultati


print("\n=== DIAGNOSTICA LUMSA V2 ===\n")
sessione = crea_sessione()
totale = 0

for pagina in PAGINE_LUMSA:
    print("\n========================================")
    print("SEZIONE:", pagina["nome"])
    print("========================================")
    try:
        html = scarica(sessione, pagina["url"])
        totale += len(analizza_pagina(pagina, html))
    except Exception as errore:
        print("ERRORE NELLA SEZIONE:", pagina["nome"])
        print(str(errore))

print("\nTOTALE CANDIDATI PERTINENTI:", totale)
print("\n=== FINE DIAGNOSTICA LUMSA V2 ===")
