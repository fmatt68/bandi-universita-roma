import hashlib
import json
import os
import re
import smtplib
from datetime import date, datetime
from email.mime.text import MIMEText
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


FILE_STORICO = "storico_romatre.json"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

PAGINE_ROMATRE = [
    {
        "nome": "Dipartimento di Scienze - Incarichi di insegnamento",
        "url": (
            "https://scienze.uniroma3.it/dipartimento/bandi-e-concorsi/"
            "bandi-per-incarichi-di-insegnamento/"
        ),
        "area_predefinita": "Scienze biologiche e naturali",
    },
    {
        "nome": "Dipartimento di Matematica e Fisica - Incarichi didattici",
        "url": (
            "https://matematicafisica.uniroma3.it/dipartimento/"
            "bandi-e-concorsi/bandi-per-incarichi-di-insegnamento-"
            "e-di-didattica-integrativa/"
        ),
        "area_predefinita": "Matematica, Fisica e Informatica",
    },
    {
        "nome": "Ingegneria Civile, Informatica e Tecnologie Aeronautiche",
        "url": (
            "https://ingegneriacivileinformaticatecnologieaeronautiche."
            "uniroma3.it/dipartimento/bandi-e-concorsi/"
        ),
        "area_predefinita": "Informatica e Ingegneria",
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

PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "incarico didattico",
    "incarichi didattici",
    "didattica integrativa",
    "supporto alla didattica",
    "attivita didattica",
    "attività didattica",
    "conferimento di incarichi didattici",
    "conferimento di incarichi di insegnamento",
]

PAROLE_APERTURA_BLOCCO = [
    "bando",
    "avviso",
    "procedura selettiva",
    "procedura di selezione",
    "selezione pubblica",
    "ricognizione interna",
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
    "info-",
    "biologia",
    "biotecnologie",
    "biochimica",
    "bioinformatica",
    "fisica",
    "informatica",
    "ingegneria biomedica",
    "bioingegneria",
    "scienze biologiche",
    "scienze della vita",
    "laboratorio",
]

PAROLE_INTERNE = [
    "ricognizione interna",
    "personale interno",
    "personale dell'ateneo",
    "personale dell’ateneo",
    "personale in servizio presso",
    "mansioni esigibili da personale dell'ateneo",
    "mansioni esigibili da personale dell’ateneo",
]

PAROLE_FASI_SUCCESSIVE = [
    "avviso colloquio",
    "avviso di colloquio",
    "discussione pubblica",
    "commissione",
    "verbale",
    "approvazione atti",
    "approvazione degli atti",
    "graduatoria",
    "esito valutazione",
    "esito ricognizione",
    "assegnazione",
    "vincitore",
    "vincitrice",
    "rettifica",
    "convocazione",
    "rinuncia",
    "revoca",
]

PAROLE_ACCESSORIE = [
    "allegato",
    "fac-simile",
    "fac simile",
    "modello cv",
    "domanda di partecipazione",
    "autocertificazione",
    "informativa privacy",
]

MESI = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


def normalizza_testo(testo):
    if testo is None:
        return ""
    return " ".join(unescape(str(testo)).split())


def contiene(testo, parole):
    testo_lower = testo.lower()
    return any(parola in testo_lower for parola in parole)


def normalizza_link(base_url, href):
    link = urljoin(base_url, href)
    parti = urlsplit(link)
    return urlunsplit((parti.scheme, parti.netloc, parti.path, parti.query, ""))


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
    risposta.raise_for_status()
    print("Pagina letta:", risposta.url)
    return risposta.text


def carica_storico():
    try:
        with open(FILE_STORICO, "r", encoding="utf-8") as file:
            storico = json.load(file)
        if not isinstance(storico, dict):
            raise ValueError("Formato storico non valido")
        if not isinstance(storico.get("bandi_gia_segnalati"), list):
            storico["bandi_gia_segnalati"] = []
        return storico
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {"bandi_gia_segnalati": []}


def salva_storico(storico):
    with open(FILE_STORICO, "w", encoding="utf-8") as file:
        json.dump(storico, file, indent=2, ensure_ascii=False)


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
        ".entry-content",
        ".page-content",
        ".content-area",
        "[role='main']",
    ]
    for selettore in selettori:
        elemento = soup.select_one(selettore)
        if elemento is None:
            continue
        testo = normalizza_testo(elemento.get_text(" ", strip=True))
        if len(testo) >= 50:
            return elemento
    return soup.body or soup


def estrai_righe(contenuto):
    testo = contenuto.get_text("\n", strip=True)
    righe = []
    for riga in testo.splitlines():
        riga = normalizza_testo(riga)
        if not riga:
            continue
        if riga.lower().startswith("link identifier"):
            continue
        if righe and riga == righe[-1]:
            continue
        righe.append(riga)
    return righe


def e_inizio_bando(riga):
    riga_lower = riga.lower()
    return any(
        riga_lower.startswith(parola)
        for parola in PAROLE_APERTURA_BLOCCO
    )


def crea_blocchi(righe):
    blocchi = []
    corrente = None

    for riga in righe:
        if e_inizio_bando(riga):
            if corrente is not None:
                blocchi.append(corrente)
            corrente = [riga]
            continue

        if corrente is not None:
            corrente.append(riga)
            if len(corrente) >= 18:
                blocchi.append(corrente)
                corrente = None

    if corrente is not None:
        blocchi.append(corrente)

    return [normalizza_testo(" ".join(blocco)) for blocco in blocchi]


def estrai_date(testo):
    date_trovate = []

    pattern_numerico = re.compile(
        r"(?:scadenza|termine|entro\s+e\s+non\s+oltre)"
        r"[^0-9]{0,100}(\d{1,2})[/.](\d{1,2})[/.](\d{4})",
        re.IGNORECASE,
    )

    pattern_testuale = re.compile(
        r"(?:scadenza|termine|entro\s+e\s+non\s+oltre)"
        r"[^0-9]{0,120}(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
        r"settembre|ottobre|novembre|dicembre)\s+(\d{4})",
        re.IGNORECASE,
    )

    for giorno, mese, anno in pattern_numerico.findall(testo):
        try:
            valore = date(int(anno), int(mese), int(giorno))
            if valore not in date_trovate:
                date_trovate.append(valore)
        except ValueError:
            continue

    for giorno, mese_testo, anno in pattern_testuale.findall(testo):
        try:
            valore = date(
                int(anno),
                MESI[mese_testo.lower()],
                int(giorno),
            )
            if valore not in date_trovate:
                date_trovate.append(valore)
        except (ValueError, KeyError):
            continue

    return date_trovate


def scegli_scadenza(date_trovate):
    if not date_trovate:
        return None
    future = [valore for valore in date_trovate if valore >= date.today()]
    if future:
        return min(future)
    return max(date_trovate)


def estrai_link_documenti(contenuto, url_pagina):
    links = []
    for ancora in contenuto.find_all("a", href=True):
        titolo = normalizza_testo(ancora.get_text(" ", strip=True))
        link = normalizza_link(url_pagina, ancora.get("href", ""))
        link_lower = link.lower()
        if not any(
            indicatore in link_lower
            for indicatore in [".pdf", ".doc", ".docx", "traspare.com/news/"]
        ):
            continue
        if contiene(titolo, PAROLE_ACCESSORIE):
            continue
        links.append({"titolo": titolo, "link": link})
    return links


def scegli_link_bando(blocco, links, url_pagina):
    parole_titolo = {
        parola
        for parola in re.findall(r"[a-z0-9-]+", blocco.lower())
        if len(parola) >= 5
    }

    migliore = None
    punteggio_migliore = -1

    for voce in links:
        testo_link = f"{voce['titolo']} {voce['link']}".lower()
        parole_link = set(re.findall(r"[a-z0-9-]+", testo_link))
        punteggio = len(parole_titolo & parole_link)
        if "bando" in testo_link:
            punteggio += 4
        if "avviso" in testo_link:
            punteggio += 2
        if punteggio > punteggio_migliore:
            punteggio_migliore = punteggio
            migliore = voce["link"]

    return migliore or url_pagina


def estrai_titolo(blocco):
    separatori = [" Scadenza", " scadenza", " SCADENZA"]
    titolo = blocco
    for separatore in separatori:
        if separatore in titolo:
            titolo = titolo.split(separatore, 1)[0]
    return titolo[:500].strip()


def crea_identificativo(url_pagina, titolo, scadenza):
    testo = f"{url_pagina}|{titolo}|{scadenza.isoformat()}"
    impronta = hashlib.sha256(testo.encode("utf-8")).hexdigest()[:20]
    return f"{url_pagina}#bando-{impronta}"


def analizza_pagina(sessione, pagina):
    try:
        html = scarica_pagina(sessione, pagina["url"])
    except Exception as errore:
        print("ERRORE FONTE:", pagina["nome"], str(errore))
        return [], False

    soup = BeautifulSoup(html, "html.parser")
    pulisci_pagina(soup)
    contenuto = trova_contenuto_principale(soup)
    righe = estrai_righe(contenuto)
    blocchi = crea_blocchi(righe)
    documenti = estrai_link_documenti(contenuto, pagina["url"])

    print("Blocchi candidati:", len(blocchi))
    risultati = []

    for blocco in blocchi:
        if contiene(blocco, PAROLE_INTERNE):
            print("ESCLUSA ricognizione interna:", estrai_titolo(blocco))
            continue

        if contiene(blocco, PAROLE_FASI_SUCCESSIVE):
            continue

        prima_fascia = contiene(blocco, PAROLE_PRIMA_FASCIA)
        docenza = contiene(blocco, PAROLE_DOCENZA)

        if not (prima_fascia or docenza):
            continue

        area_esplicita = contiene(blocco, PAROLE_AREA)

        # Le pagine monitorate appartengono già a dipartimenti scientifici
        # selezionati. L'area esplicita viene conservata come informazione,
        # ma non è obbligatoria per gli incarichi didattici della pagina.
        if not (area_esplicita or pagina["area_predefinita"]):
            continue

        scadenza = scegli_scadenza(estrai_date(blocco))

        if scadenza is None:
            print("IGNORATO senza scadenza:", estrai_titolo(blocco))
            continue

        if scadenza < date.today():
            continue

        titolo = estrai_titolo(blocco)
        link_documento = scegli_link_bando(
            blocco,
            documenti,
            pagina["url"],
        )
        identificativo = crea_identificativo(
            pagina["url"],
            titolo,
            scadenza,
        )

        risultati.append(
            {
                "id": identificativo,
                "titolo": titolo,
                "tipologia": (
                    "Prima fascia"
                    if prima_fascia
                    else "Docenza/incarico didattico"
                ),
                "area": pagina["area_predefinita"],
                "area_esplicita": area_esplicita,
                "scadenza": scadenza,
                "pagina": pagina["url"],
                "documento": link_documento,
                "descrizione": blocco[:1800],
            }
        )

    return risultati, True


def invia_email(bandi):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("CREDENZIALI EMAIL NON CONFIGURATE")
        return False

    righe = [
        "Nuovi bandi Roma Tre",
        "",
        "Sono state individuate nuove procedure aperte e pertinenti.",
        "",
    ]

    for numero, bando in enumerate(bandi, start=1):
        righe.extend(
            [
                "========================================",
                f"BANDO {numero}",
                "========================================",
                f"Tipologia: {bando['tipologia']}",
                f"Area: {bando['area']}",
                f"Scadenza: {bando['scadenza'].strftime('%d/%m/%Y')}",
                "",
                bando["titolo"],
                "",
                bando["descrizione"],
                "",
                "Pagina dipartimentale:",
                bando["pagina"],
                "",
                "Documento o pagina del bando:",
                bando["documento"],
                "",
            ]
        )

    email = MIMEText(
        "\n".join(righe),
        "plain",
        "utf-8",
    )
    email["Subject"] = "[ROMA TRE] Nuovi bandi"
    email["From"] = EMAIL_ADDRESS
    email["To"] = EMAIL_ADDRESS

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=60,
    )

    try:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(email)
    finally:
        server.quit()

    print("EMAIL INVIATA")
    return True


print("\n=== MONITOR ROMA TRE ===\n")

sessione = crea_sessione()
storico = carica_storico()
gia_segnalati = set(storico["bandi_gia_segnalati"])

bandi = []
fonti_non_accessibili = []

for pagina in PAGINE_ROMATRE:
    print("\nControllo:", pagina["nome"])
    risultati, fonte_ok = analizza_pagina(sessione, pagina)
    if not fonte_ok:
        fonti_non_accessibili.append(pagina["nome"])
        continue
    bandi.extend(risultati)

if fonti_non_accessibili:
    print("\nATTENZIONE: fonti non accessibili:")
    for nome in fonti_non_accessibili:
        print("-", nome)
    raise RuntimeError(
        "Monitor Roma Tre incompleto: una o più fonti non sono accessibili"
    )

bandi_unici = {bando["id"]: bando for bando in bandi}
bandi = sorted(
    bandi_unici.values(),
    key=lambda elemento: (
        elemento["scadenza"],
        elemento["titolo"],
    ),
)

nuovi = [
    bando
    for bando in bandi
    if bando["id"] not in gia_segnalati
]

print("\nBandi aperti pertinenti:", len(bandi))
print("Nuovi bandi da segnalare:", len(nuovi))

for bando in nuovi:
    print("\nNUOVO BANDO:")
    print("Titolo:", bando["titolo"])
    print("Tipologia:", bando["tipologia"])
    print("Area:", bando["area"])
    print("Scadenza:", bando["scadenza"].strftime("%d/%m/%Y"))
    print("Pagina:", bando["pagina"])
    print("Documento:", bando["documento"])

if not nuovi:
    print("NESSUN NUOVO BANDO")
else:
    email_inviata = invia_email(nuovi)

    if email_inviata:
        storico["bandi_gia_segnalati"].extend(
            bando["id"]
            for bando in nuovi
        )
        storico["bandi_gia_segnalati"] = list(
            dict.fromkeys(
                storico["bandi_gia_segnalati"]
            )
        )
        salva_storico(storico)
        print("STORICO ROMA TRE AGGIORNATO")
    else:
        print(
            "Storico non aggiornato perché "
            "l'email non è stata inviata"
        )

print("\n=== FINE MONITOR ROMA TRE ===")
