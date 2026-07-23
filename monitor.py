import requests

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

print("Status code:", response.status_code)

testo = response.text

print(
    "IELTS presente:",
    "Instructor per corsi di preparazione esami IELTS" in testo
)

print(
    "Data scadenza presente:",
    "Data scadenza bando" in testo
)
