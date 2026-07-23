import os
import smtplib
from email.mime.text import MIMEText

def invia_email(oggetto, testo):
    email = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_PASSWORD")

    msg = MIMEText(testo)
    msg["Subject"] = oggetto
    msg["From"] = email
    msg["To"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, password)
    server.send_message(msg)
    server.quit()

bandi_trovati = [
    {
        "priorita": "ALTA",
        "titolo": "Bando di prova",
        "scadenza": "31/12/2026"
    }
]

testo = ""

for bando in bandi_trovati:
    testo += f"[{bando['priorita']}]\n"
    testo += f"Titolo: {bando['titolo']}\n"
    testo += f"Scadenza: {bando['scadenza']}\n\n"

invia_email(
    "Monitor Bandi Universitari - Test",
    testo
)

print("Email inviata")
