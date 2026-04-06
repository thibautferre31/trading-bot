import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject, body):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    sender = os.getenv("SMTP_SENDER")
    password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("SMTP_RECIPIENT")

    if not smtp_host or not sender or not password or not recipient:
        print("Variables SMTP manquantes.")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        print(f"Email envoyé à {recipient}")

    except Exception as e:
        print(f"Erreur envoi email : {e}")
