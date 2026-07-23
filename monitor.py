import requests

url = "https://web.uniroma1.it/trasparenza/bandi_concorso_docenti/66?field_user_centro_spesa_ugov_tid=All&field_data_pubblicazione_value%5Bvalue%5D%5Byear%5D=&field_bis_sc_e_ssd_tid=All&keys=&field_bis_gsd_ssd_target_id=All"

response = requests.get(url)

testo = response.text.lower()

print("pdf presente:", ".pdf" in testo)
print("sites/default/files presente:", "sites/default/files" in testo)
print("bando presente:", "bando_7-2026" in testo)
``
