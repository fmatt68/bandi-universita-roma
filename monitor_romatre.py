import re

from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.uniroma3.it"


PAGINE_ROMATRE = [
    {
        "nome": (
            "Ateneo - Concorsi personale "
            "docente e ricercatore"
        ),
        "tipo": "professori",
        "url": (
            "https://www.uniroma3.it/servizi/"
            "servizi-al-personale/portale-del-personale/"
            "concorsi-e-selezioni/"
            "concorsi-personale-docente-e-ricercatore/"
        )
    },
    {
        "nome": (
            "Dipartimento di Scienze "
            "- Bandi e concorsi"
        ),
        "tipo": "docenza",
        "url": (
            "https://scienze.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
        )
    },
    {
        "nome": (
            "Dipartimento di Scienze "
            "- Incarichi di insegnamento"
        ),
        "tipo": "docenza",
        "url": (
            "https://scienze.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
            "bandi-per-incarichi-di-insegnamento/"
        )
    },
    {
        "nome": (
            "Dipartimento di Matematica e Fisica "
            "- Incarichi didattici"
        ),
        "tipo": "docenza",
        "url": (
            "https://matematicafisica.uniroma3.it/"
            "dipartimento/bandi-e-concorsi/"
            "bandi-per-incarichi-di-insegnamento-"
            "e-di-didattica-integrativa/"
        )
    },
    {
        "nome": (
            "Ingegneria Civile, Informatica "
            "e Tecnologie Aeronautiche"
        ),
        "tipo": "docenza",
        "url": (
            "https://ingegneriacivileinformaticatecnologieaeronautiche."
            "uniroma3.it/dipartimento/bandi-e-concorsi/"
        )
    }
]


PAROLE_PRIMA_FASCIA = [
    "prima fascia",
    "i fascia",
    "professore ordinario",
    "professoressa ordinaria",
    "professore di ruolo di prima fascia",
    "professoressa di ruolo di prima fascia",
    "chiamata di professore di prima fascia",
    "chiamata di professori di prima fascia"
]


PAROLE_DOCENZA = [
    "docente a contratto",
    "docenti a contratto",
    "docenza a contratto",
    "professore a contratto",
    "professoressa a contratto",
    "professori a contratto",
    "incarico di insegnamento",
    "incarichi di insegnamento",
    "conferimento di incarichi di insegnamento",
    "conferimento incarichi di insegnamento",
    "incarico didattico",
    "incarichi didattici",
    "didattica integrativa",
    "supporto alla didattica",
    "attivita didattica",
    "attività didattica",
    "selezione per titoli"
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
    "laboratorio"
]


PAROLE_ACCESSORIE = [
    "allegato",
    "allegato 1",
    "allegato 2",
    "fac-simile",
    "fac simile",
    "modello cv",
    "domanda di partecipazione",
    "autocertificazione",
    "esito",
    "esito valutazione",
    "graduatoria",
    "vincitori",
    "commissione",
    "verbale",
    "approvazione atti"
]


PAROLE_RICOGNIZIONE_INTERNA = [
    "ricognizione interna",
    "personale interno",
    "personale in servizio presso",
    "risorse interne all'ateneo",
    "risorse interne all’ateneo"
]


MESI_ITALIANI = (
    "gennaio|febbraio|marzo|aprile|maggio|"
    "giugno|luglio|agosto|settembre|ottobre|"
    "novembre|dicembre"
)


def crea_sessione():

    sessione = requests.Session()

    sessione.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": (
                "it-IT"
