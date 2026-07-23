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

invia_email(
    "Test Sistema Bandi",
    "Ciao Fabrizio, il sistema è pronto per il monitoraggio."
)

print("Email inviata")
