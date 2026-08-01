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


FILE_STORICO = "storico_lumsa.json"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

PAGINE_LUMSA = [
    {
        "nome": "Docenze a contratto - Albo degli idonei",
        "url": "https://lumsa.it/it/docenze-a-contratto-albo-degli-idonei",
        "area_predefinita": "Docenze a contratto LUMSA",
    },
    {
        "nome": "Reclutamento docenti, ricercatori e tutor",
        "url": "https://lumsa.it/it/reclutamento-docenti-ricercatori-e-tutor",
        "area_predefinita": "Reclutamento accademico LUMSA",
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
    "conferimento degli incarichi di insegnamento",
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
    "approvazione degli atti",
    "regolamento",
    "tabella compensi",
    "allegato",
    "modello cv",
    "domanda di partecipazione",
    "rettifica",
    "revoca",
    "rinuncia",
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


def scarica(sessione, url):
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
    for selettore in [
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
    ]:
        for elemento in soup.select(selettore):
            elemento.decompose()


def trova_contenuto_principale(soup):
    for selettore in [
        "main",
        "article",
        "#content",
        "#main-content",
        ".page-content",
        ".entry-content",
        ".content-area",
        "[role='main']",
    ]:
        elemento = soup.select_one(selettore)
        if elemento is None:
            continue
        testo = normalizza_testo(elemento.get_text(" ", strip=True))
        if len(testo) >= 100:
            return elemento
    return soup.body or soup


def estrai_righe(contenuto):
    righe = []
    for riga in contenuto.get_text("\n", strip=True).splitlines():
        riga = normalizza_testo(riga)
        if not riga:
            continue
        if righe and riga == righe[-1]:
            continue
        righe.append(riga)
    return righe


def inizia_blocco(riga):
    riga_lower = riga.lower()
    return any(parola in riga_lower for parola in PAROLE_APERTURA)


def crea_blocchi(righe):
    indici = [indice for indice, riga in enumerate(righe) if inizia_blocco(riga)]
    blocchi = []

    for posizione, indice_inizio in enumerate(indici):
        if posizione + 1 < len(indici):
            indice_fine = indici[posizione + 1]
        else:
            indice_fine = min(len(righe), indice_inizio + 30)

        testo = normalizza_testo(" ".join(righe[indice_inizio:indice_fine]))
        if testo:
            blocchi.append(testo)

    return blocchi


def converti_data(giorno, mese, anno):
    try:
        if isinstance(mese, str) and not mese.isdigit():
            mese_numero = MESI[mese.lower()]
        else:
            mese_numero = int(mese)
        return date(int(anno), mese_numero, int(giorno))
    except (ValueError, KeyError):
        return None


def estrai_date_scadenza(testo):
    trovate = []

    pattern_numerico = re.compile(
        r"scadenza(?:\s+presentazione\s+(?:delle\s+)?domande)?"
        r"[^0-9]{0,80}(\d{1,2})[/.](\d{1,2})[/.](\d{4})",
        re.IGNORECASE,
    )
    pattern_testuale = re.compile(
        r"(?:scadenza(?:\s+presentazione\s+(?:delle\s+)?domande)?|"
        r"entro\s+(?:e\s+non\s+oltre\s+)?)"
        r"[^0-9]{0,100}(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
        r"settembre|ottobre|novembre|dicembre)\s+(\d{4})",
        re.IGNORECASE,
    )

    for giorno, mese, anno in pattern_numerico.findall(testo):
        valore = converti_data(giorno, mese, anno)
        if valore is not None and valore not in trovate:
            trovate.append(valore)

    for giorno, mese, anno in pattern_testuale.findall(testo):
        valore = converti_data(giorno, mese, anno)
        if valore is not None and valore not in trovate:
            trovate.append(valore)

    return trovate


def scegli_scadenza(date_trovate):
    if not date_trovate:
        return None
    future = [valore for valore in date_trovate if valore >= date.today()]
    return min(future) if future else max(date_trovate)


def titolo_blocco(blocco):
    for separatore in [" Scadenza", " scadenza", " SCADENZA"]:
        if separatore in blocco:
            return blocco.split(separatore, 1)[0][:600].strip()
    return blocco[:600].strip()


def estrai_link_documenti(contenuto, pagina_url):
    risultati = []
    for ancora in contenuto.find_all("a", href=True):
        titolo = normalizza_testo(ancora.get_text(" ", strip=True))
        link = normalizza_link(pagina_url, ancora.get("href", ""))
        if not any(est in link.lower() for est in [".pdf", ".doc", ".docx"]):
            continue
        risultati.append({"titolo": titolo, "link": link})
    return risultati


def scegli_documento(blocco, documenti, pagina_url):
    parole_blocco = {
        parola
        for parola in re.findall(r"[a-z0-9-]+", blocco.lower())
        if len(parola) >= 5
    }
    migliore = None
    punteggio_migliore = -1

    for documento in documenti:
        testo_documento = f"{documento['titolo']} {documento['link']}".lower()
        parole_documento = set(re.findall(r"[a-z0-9-]+", testo_documento))
        punteggio = len(parole_blocco & parole_documento)
        if "manifestazione" in testo_documento:
            punteggio += 5
        if "bando" in testo_documento:
            punteggio += 4
        if contiene(documento["titolo"], PAROLE_DA_ESCLUDERE):
            punteggio -= 8
        if punteggio > punteggio_migliore:
            punteggio_migliore = punteggio
            migliore = documento["link"]

    return migliore or pagina_url


def crea_identificativo(pagina_url, titolo, scadenza):
    testo = f"{pagina_url}|{titolo}|{scadenza.isoformat()}"
    impronta = hashlib.sha256(testo.encode("utf-8")).hexdigest()[:20]
    return f"{pagina_url}#bando-{impronta}"


def analizza_pagina(sessione, pagina):
    try:
        html = scarica(sessione, pagina["url"])
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
        if contiene(blocco, PAROLE_DA_ESCLUDERE):
            continue

        docenza = contiene(blocco, PAROLE_DOCENZA)
        prima_fascia = contiene(blocco, PAROLE_PRIMA_FASCIA)
        if not (docenza or prima_fascia):
            continue

        scadenza = scegli_scadenza(estrai_date_scadenza(blocco))
        if scadenza is None:
            print("IGNORATO senza scadenza:", titolo_blocco(blocco))
            continue
        if scadenza < date.today():
            continue

        titolo = titolo_blocco(blocco)
        area = contiene(blocco, PAROLE_AREA)
        documento = scegli_documento(blocco, documenti, pagina["url"])
        identificativo = crea_identificativo(pagina["url"], titolo, scadenza)

        risultati.append(
            {
                "id": identificativo,
                "titolo": titolo,
                "tipologia": "Prima fascia" if prima_fascia else "Docenza a contratto",
                "area_interesse": area,
                "scadenza": scadenza,
                "pagina": pagina["url"],
                "documento": documento,
                "descrizione": blocco[:1800],
            }
        )

    return risultati, True


def invia_email(bandi):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("CREDENZIALI EMAIL NON CONFIGURATE")
        return False

    righe = [
        "Nuovi bandi LUMSA",
        "",
        "Sono state individuate nuove procedure aperte di interesse.",
        "",
    ]

    for numero, bando in enumerate(bandi, start=1):
        righe.extend(
            [
                "========================================",
                f"BANDO {numero}",
                "========================================",
                f"Tipologia: {bando['tipologia']}",
                "Area disciplinare esplicita: "
                + ("Sì" if bando["area_interesse"] else "Non individuata"),
                f"Scadenza: {bando['scadenza'].strftime('%d/%m/%Y')}",
                "",
                bando["titolo"],
                "",
                bando["descrizione"],
                "",
                "Pagina ufficiale:",
                bando["pagina"],
                "",
                "Documento principale:",
                bando["documento"],
                "",
            ]
        )

    email = MIMEText("\n".join(righe), "plain", "utf-8")
    email["Subject"] = "[LUMSA] Nuovi bandi"
    email["From"] = EMAIL_ADDRESS
    email["To"] = EMAIL_ADDRESS

    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=60)
    try:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(email)
    finally:
        server.quit()

    print("EMAIL INVIATA")
    return True


print("\n=== MONITOR LUMSA ===\n")

sessione = crea_sessione()
storico = carica_storico()
gia_segnalati = set(storico["bandi_gia_segnalati"])
bandi = []
fonti_non_accessibili = []

for pagina in PAGINE_LUMSA:
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
    raise RuntimeError("Monitor LUMSA incompleto: fonte non accessibile")

bandi_unici = {bando["id"]: bando for bando in bandi}
bandi = sorted(
    bandi_unici.values(),
    key=lambda elemento: (elemento["scadenza"], elemento["titolo"]),
)
nuovi = [bando for bando in bandi if bando["id"] not in gia_segnalati]

print("\nBandi aperti pertinenti:", len(bandi))
print("Nuovi bandi da segnalare:", len(nuovi))

for bando in nuovi:
    print("\nNUOVO BANDO:")
    print("Titolo:", bando["titolo"])
    print("Tipologia:", bando["tipologia"])
    print("Scadenza:", bando["scadenza"].strftime("%d/%m/%Y"))
    print("Pagina:", bando["pagina"])
    print("Documento:", bando["documento"])

if not nuovi:
    print("NESSUN NUOVO BANDO")
else:
    if invia_email(nuovi):
        storico["bandi_gia_segnalati"].extend(bando["id"] for bando in nuovi)
        storico["bandi_gia_segnalati"] = list(
            dict.fromkeys(storico["bandi_gia_segnalati"])
        )
        salva_storico(storico)
        print("STORICO LUMSA AGGIORNATO")
    else:
        print("Storico non aggiornato perché l'email non è stata inviata")

print("\n=== FINE MONITOR LUMSA ===")
