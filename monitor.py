import os
import smtplib
from email.mime.text import MIMEText

email = os.environ.get("EMAIL_ADDRESS")
password = os.environ.get("EMAIL_PASSWORD")

msg = MIMEText("Ciao Fabrizio,\n\nil sistema GitHub funziona correttamente.")
msg["Subject"] = "Test GitHub Bandi"
msg["From"] = email
msg["To"] = email

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(email, password)

server.send_message(msg)

server.quit()

print("Email inviata con successo")
