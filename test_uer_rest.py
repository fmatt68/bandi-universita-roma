import json
from urllib.parse import urlencode

import requests


ENDPOINTS = [
    {
        "nome": "Indice API WordPress",
        "url": "https://www.uer.it/wp-json/",
    },
    {
        "nome": "Ricerca pagine docenti a contratto",
        "url": (
            "https://www.uer.it/wp-json/wp/v2/search?"
            + urlencode(
                {
                    "search": "docenti a contratto",
                    "per_page": 20,
                }
            )
        ),
    },
    {
        "nome": "Pagina docenti a contratto tramite slug",
        "url": (
            "https://www.uer.it/wp-json/wp/v2/pages?"
            + urlencode(
                {
                    "slug": (
                        "bandi-per-il-reclutamento-di-docenti-a-contratto-"
                        "art-23-comma-2-della-l-n-240-2010"
                    ),
                    "per_page": 10,
                }
            )
        ),
    },
    {
        "nome": "Pagina professori I e II fascia tramite slug",
        "url": (
            "https://www.uer.it/wp-json/wp/v2/pages?"
            + urlencode(
                {
                    "slug": (
                        "bandi-per-il-reclutamento-di-professori-di-i-e-di-"
                        "ii-fascia-art-18-della-l-n-240-2010"
                    ),
                    "per_page": 10,
                }
            )
        ),
    },
    {
        "nome": "Ricerca prima fascia",
        "url": (
            "https://www.uer.it/wp-json/wp/v2/search?"
            + urlencode(
                {
                    "search": "prima fascia",
                    "per_page": 20,
                }
            )
        ),
    },
]


def crea_sessione():
    sessione = requests.Session()
    sessione.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        }
    )
    return sessione


def riassumi_json(dati):
    if isinstance(dati, list):
        print("TIPO JSON: lista")
        print("ELEMENTI:", len(dati))

        for indice, elemento in enumerate(dati[:5], start=1):
            print(f"\nELEMENTO {indice}:")

            if not isinstance(elemento, dict):
                print(str(elemento)[:1000])
                continue

            for chiave in [
                "id",
                "title",
                "url",
                "slug",
                "subtype",
                "type",
                "status",
                "link",
            ]:
                if chiave in elemento:
                    valore = elemento[chiave]

                    if isinstance(valore, dict):
                        valore = valore.get("rendered", valore)

                    print(
                        f"{chiave.upper()}:",
                        str(valore)[:1000],
                    )

    elif isinstance(dati, dict):
        print("TIPO JSON: oggetto")
        print("CHIAVI PRINCIPALI:", list(dati.keys())[:50])

        namespaces = dati.get("namespaces")

        if isinstance(namespaces, list):
            print("NAMESPACES:", namespaces[:50])

        routes = dati.get("routes")

        if isinstance(routes, dict):
            print("NUMERO ROUTES:", len(routes))

            routes_utili = [
                route
                for route in routes
                if any(
                    parola in route.lower()
                    for parola in [
                        "wp/v2/pages",
                        "wp/v2/search",
                        "post",
                        "page",
                    ]
                )
            ]

            print("ROUTES UTILI:", routes_utili[:50])

    else:
        print("TIPO JSON:", type(dati).__name__)
        print(str(dati)[:2000])


def prova_endpoint(sessione, endpoint):
    print("\n========================================")
    print("ENDPOINT:", endpoint["nome"])
    print("URL:", endpoint["url"])
    print("========================================")

    try:
        risposta = sessione.get(
            endpoint["url"],
            timeout=60,
            allow_redirects=True,
        )
    except requests.RequestException as errore:
        print("STATO: ERRORE DI CONNESSIONE")
        print("ERRORE:", str(errore))
        return False

    print("STATUS CODE:", risposta.status_code)
    print("URL FINALE:", risposta.url)
    print("CONTENT-TYPE:", risposta.headers.get("Content-Type"))
    print("DIMENSIONE RISPOSTA:", len(risposta.content))

    if risposta.status_code != 200:
        print("STATO: FONTE NON ACCESSIBILE")
        print("PRIMI CARATTERI RISPOSTA:")
        print(risposta.text[:1200])
        return False

    try:
        dati = risposta.json()
    except json.JSONDecodeError:
        print("STATO: RISPOSTA 200 MA NON JSON")
        print("PRIMI CARATTERI RISPOSTA:")
        print(risposta.text[:1500])
        return False

    print("STATO: JSON ACCESSIBILE")
    riassumi_json(dati)
    return True


print("\n=== TEST API REST UER ===\n")

sessione = crea_sessione()
risultati = []

for endpoint in ENDPOINTS:
    accessibile = prova_endpoint(sessione, endpoint)
    risultati.append(
        {
            "nome": endpoint["nome"],
            "accessibile": accessibile,
        }
    )

numero_accessibili = sum(
    1
    for risultato in risultati
    if risultato["accessibile"]
)

print("\n========================================")
print("RIEPILOGO FINALE")
print("========================================")

for risultato in risultati:
    print(
        risultato["nome"] + ":",
        "ACCESSIBILE"
        if risultato["accessibile"]
        else "NON ACCESSIBILE",
    )

print("\nENDPOINT ACCESSIBILI:", numero_accessibili)
print("ENDPOINT TOTALI:", len(risultati))

if numero_accessibili == 0:
    print(
        "\nESITO: le API REST UER non sono utilizzabili "
        "da GitHub Actions."
    )
else:
    print(
        "\nESITO: almeno un endpoint REST UER è accessibile. "
        "È possibile tentare il monitor tramite API."
    )

print("\n=== FINE TEST API REST UER ===")
