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

BASE_URL = "https://uniroma3.traspare.com"
PAGINE_FONTE = [
    "https://uniroma3.traspare.com/",
    "https://uniroma3.traspare.com/albo",
]
FILE_STORICO = "storico_romatre.json"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

PAROLE_PRIMA_FASCIA = [
    "prima fascia", "i fascia", "professore ordinario",
    "professoressa ordinaria", "professore di ruolo di prima fascia",
    "professoressa di ruolo di prima fascia",
]
PAROLE_DOCENZA = [
    "docente a contratto", "docenti a contratto", "docenza a contratto",
    "professore a contratto", "professoressa a contratto",
    "incarico di insegnamento", "incarichi di insegnamento",
    "incarico didattico", "incarichi didattici", "didattica integrativa",
    "supporto alla didattica", "attivita didattica", "attività didattica",
    "conferimento di incarichi didattici",
    "conferimento di incarichi di insegnamento",
]
PAROLE_AREA = [
    "meds-", "medf-", "bios-", "mvet-", "iinf-", "phys-", "ibio-",
    "bio/", "med/", "vet/", "fis/", "ing-inf/", "info-",
    "biologia", "biotecnologie", "biochimica", "bioinformatica",
    "fisica", "informatica", "ingegneria biomedica", "bioingegneria",
    "scienze biologiche", "scienze della vita", "laboratorio",
]
DIPARTIMENTI_INTERESSE = [
    "dipartimento di scienze", "dipartimento di matematica e fisica",
    "matematica e fisica", "ingegneria civile, informatica",
    "ingegneria civile e informatica", "tecnologie aeronautiche",
    "ingegneria industriale, elettronica e meccanica",
]
PAROLE_INTERNE = [
    "ricognizione interna", "personale interno", "personale dell'ateneo",
    "personale dell’ateneo", "personale in servizio presso",
    "mansioni esigibili da personale dell'ateneo",
    "mansioni esigibili da personale dell’ateneo",
]
PAROLE_FASI_SUCCESSIVE = [
    "avviso colloquio", "avviso di colloquio", "discussione pubblica",
    "commissione", "verbale", "approvazione atti", "approvazione degli atti",
    "graduatoria", "esito", "vincitore", "vincitrice", "rettifica",
    "convocazione", "rinuncia", "revoca",
]
PAROLE_ACCESSORIE = [
    "allegato", "fac-simile", "fac simile", "modello cv",
    "domanda di partecipazione", "autocertificazione", "informativa privacy",
]
MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


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


def scarica(sessione, url):
    risposta = sessione.get(url, timeout=60)
    risposta.raise_for_status()
    print("Pagina letta:", risposta.url)
    return risposta.text


def carica_storico():
    try:
        with open(FILE_STORICO, "r", encoding="utf-8") as file:
            dati = json.load(file)
        if not isinstance(dati, dict):
            raise ValueError("Storico non valido")
        if not isinstance(dati.get("bandi_gia_segnalati"), list):
            dati["bandi_gia_segnalati"] = []
        return dati
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {"bandi_gia_segnalati": []}


def salva_storico(storico):
    with open(FILE_STORICO, "w", encoding="utf-8") as file:
        json.dump(storico, file, indent=2, ensure_ascii=False)


def elimina_parti_comuni(soup):
    for selettore in [
        "script", "style", "header", "footer", "nav", "aside", "form",
        ".navbar", ".breadcrumb", ".breadcrumbs", ".sidebar", ".cookie",
        ".modal", "[role='navigation']",
    ]:
        for elemento in soup.select(selettore):
            elemento.decompose()


def estrai_link_avvisi(html, url_fonte):
    soup = BeautifulSoup(html, "html.parser")
    elimina_parti_comuni(soup)
    candidati = {}

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link = normalizza_link(url_fonte, href)
        titolo = normalizza_testo(a.get_text(" ", strip=True))
        testo_link = f"{titolo} {link}".lower()

        dettaglio_valido = (
            "/news/" in link.lower()
            or "/albo/" in link.lower()
            or "albo=" in link.lower()
            or "id=" in link.lower() and "albo" in link.lower()
        )
        if not dettaglio_valido:
            continue
        if any(x in testo_link for x in ["login", "accedi", "privacy", "cookie"]):
            continue
        if not titolo:
            titolo = "Avviso Roma Tre"
        candidati[link] = {"titolo_elenco": titolo, "link": link}

    return list(candidati.values())


def scegli_titolo(soup, titolo_elenco):
    selettori = ["h1", "h2", ".title", ".news-title", ".page-title"]
    esclusi = {"news", "albo pretorio", "avviso generico", "home"}
    for selettore in selettori:
        for nodo in soup.select(selettore):
            testo = normalizza_testo(nodo.get_text(" ", strip=True))
            if len(testo) >= 15 and testo.lower() not in esclusi:
                return testo
    return titolo_elenco


def estrai_date(testo):
    trovate = []
    pattern_num = re.compile(
        r"(?:scadenza|termine)(?:\s+presentazione\s+(?:della\s+)?domanda)?"
        r"[^0-9]{0,80}(\d{1,2})[/.](\d{1,2})[/.](\d{4})",
        re.IGNORECASE,
    )
    pattern_testo = re.compile(
        r"(?:scadenza|termine|entro\s+e\s+non\s+oltre)"
        r"[^0-9]{0,100}(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|"
        r"settembre|ottobre|novembre|dicembre)\s+(\d{4})",
        re.IGNORECASE,
    )

    for g, m, a in pattern_num.findall(testo):
        try:
            valore = date(int(a), int(m), int(g))
            if valore not in trovate:
                trovate.append(valore)
        except ValueError:
            pass

    for g, mese, a in pattern_testo.findall(testo):
        try:
            valore = date(int(a), MESI[mese.lower()], int(g))
            if valore not in trovate:
                trovate.append(valore)
        except (ValueError, KeyError):
            pass
    return trovate


def scegli_scadenza(date_trovate):
    if not date_trovate:
        return None
    future = [d for d in date_trovate if d >= date.today()]
    return min(future) if future else max(date_trovate)


def estrai_pubblicazione(testo):
    patterns = [
        re.compile(r"pubblicat[oa][^0-9]{0,30}(\d{1,2})/(\d{1,2})/(\d{4})", re.I),
        re.compile(r"avviso\s+generico[^0-9]{0,30}(\d{1,2})/(\d{1,2})/(\d{4})", re.I),
    ]
    for pattern in patterns:
        match = pattern.search(testo)
        if match:
            g, m, a = match.groups()
            try:
                return date(int(a), int(m), int(g))
            except ValueError:
                return None
    return None


def estrai_documento_principale(soup, url_dettaglio):
    possibili = []
    for a in soup.find_all("a", href=True):
        titolo = normalizza_testo(a.get_text(" ", strip=True))
        link = normalizza_link(url_dettaglio, a.get("href", ""))
        testo = f"{titolo} {link}".lower()
        if not any(est in link.lower() for est in [".pdf", ".doc", ".docx", "attachment"]):
            continue
        if contiene(titolo, PAROLE_ACCESSORIE):
            continue
        punteggio = 0
        if "bando" in testo:
            punteggio += 5
        if "avviso" in testo:
            punteggio += 3
        if contiene(testo, PAROLE_DOCENZA + PAROLE_PRIMA_FASCIA):
            punteggio += 4
        possibili.append((punteggio, link))
    if not possibili:
        return url_dettaglio
    possibili.sort(key=lambda x: x[0], reverse=True)
    return possibili[0][1]


def analizza_avviso(sessione, candidato):
    try:
        html = scarica(sessione, candidato["link"])
    except Exception as errore:
        print("Errore dettaglio:", candidato["link"], str(errore))
        return None

    soup = BeautifulSoup(html, "html.parser")
    elimina_parti_comuni(soup)
    titolo = scegli_titolo(soup, candidato["titolo_elenco"])
    testo = normalizza_testo(soup.get_text(" ", strip=True))
    testo_completo = normalizza_testo(f"{titolo} {testo} {candidato['link']}")

    if contiene(testo_completo, PAROLE_FASI_SUCCESSIVE):
        return None
    if contiene(testo_completo, PAROLE_INTERNE):
        print("ESCLUSA ricognizione interna:", titolo)
        return None

    prima_fascia = contiene(testo_completo, PAROLE_PRIMA_FASCIA)
    docenza = contiene(testo_completo, PAROLE_DOCENZA)
    if not (prima_fascia or docenza):
        return None

    area = contiene(testo_completo, PAROLE_AREA)
    dipartimento_pertinente = contiene(testo_completo, DIPARTIMENTI_INTERESSE)
    if not (area or dipartimento_pertinente):
        return None

    scadenza = scegli_scadenza(estrai_date(testo_completo))
    if scadenza is None:
        print("IGNORATO senza scadenza individuabile:", titolo)
        return None
    if scadenza < date.today():
        return None

    documento = estrai_documento_principale(soup, candidato["link"])
    pubblicazione = estrai_pubblicazione(testo_completo)

    return {
        "titolo": titolo,
        "tipologia": "Prima fascia" if prima_fascia else "Docenza/incarico didattico",
        "link": candidato["link"],
        "documento": documento,
        "scadenza": scadenza,
        "pubblicazione": pubblicazione,
        "descrizione": testo[:1600],
    }


def invia_email(bandi):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Credenziali email non configurate")
        return False

    righe = [
        "Nuovi bandi Roma Tre", "",
        "Sono state individuate nuove procedure aperte e pertinenti.", "",
    ]
    for i, bando in enumerate(bandi, 1):
        righe.extend([
            "========================================",
            f"BANDO {i}",
            "========================================",
            f"Tipologia: {bando['tipologia']}",
            "Pubblicazione: " + (
                bando["pubblicazione"].strftime("%d/%m/%Y")
                if bando["pubblicazione"] else "Non specificata"
            ),
            f"Scadenza: {bando['scadenza'].strftime('%d/%m/%Y')}",
            "", bando["titolo"], "", bando["descrizione"], "",
            "Pagina dell'avviso:", bando["link"], "",
            "Documento principale:", bando["documento"], "",
        ])

    email = MIMEText("\n".join(righe), "plain", "utf-8")
    email["Subject"] = "[ROMA TRE] Nuovi bandi"
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


print("\n=== MONITOR ROMA TRE ===\n")
sessione = crea_sessione()
storico = carica_storico()
gia_segnalati = set(storico["bandi_gia_segnalati"])

candidati = {}
for url in PAGINE_FONTE:
    try:
        html = scarica(sessione, url)
        for candidato in estrai_link_avvisi(html, url):
            candidati[candidato["link"]] = candidato
    except Exception as errore:
        print("Errore fonte:", url, str(errore))

print("Candidati Traspare individuati:", len(candidati))

bandi = []
for candidato in candidati.values():
    risultato = analizza_avviso(sessione, candidato)
    if risultato:
        bandi.append(risultato)

unici = {b["link"]: b for b in bandi}
bandi = sorted(unici.values(), key=lambda x: (x["scadenza"], x["titolo"]))
nuovi = [b for b in bandi if b["link"] not in gia_segnalati]

print("Bandi aperti pertinenti:", len(bandi))
print("Nuovi bandi da segnalare:", len(nuovi))

for bando in nuovi:
    print("\nNUOVO BANDO:")
    print("Titolo:", bando["titolo"])
    print("Tipologia:", bando["tipologia"])
    print("Scadenza:", bando["scadenza"].strftime("%d/%m/%Y"))
    print("Link:", bando["link"])

if not nuovi:
    print("NESSUN NUOVO BANDO")
else:
    if invia_email(nuovi):
        for bando in nuovi:
            storico["bandi_gia_segnalati"].append(bando["link"])
        storico["bandi_gia_segnalati"] = list(dict.fromkeys(
            storico["bandi_gia_segnalati"]
        ))
        salva_storico(storico)
        print("STORICO ROMA TRE AGGIORNATO")
    else:
        print("Storico non aggiornato per mancato invio email")

print("\n=== FINE MONITOR ROMA TRE ===")
