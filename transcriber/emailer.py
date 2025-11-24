"""Email sending (Gmail SMTP)."""
import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from . import logger


def send_transcription_email(gmail_app_password: str | None, gmail_sender_email: str | None, email_to: str | None, subject: str, body_text: str, attachment_path: str | None):
    if not gmail_app_password or not gmail_sender_email or not email_to:
        logger.info("Missing email configuration; skipping email.")
        return False
    message = MIMEMultipart()
    message["From"] = gmail_sender_email
    message["To"] = email_to
    message["Subject"] = subject
    message.attach(MIMEText(body_text, "plain", "utf-8"))
    if attachment_path and os.path.exists(attachment_path):
        part = MIMEBase('application', 'octet-stream')
        with open(attachment_path, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
        message.attach(part)
    context = ssl.create_default_context()
    smtp_server = "smtp.gmail.com"
    port = 465
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(gmail_sender_email, gmail_app_password)
            server.sendmail(gmail_sender_email, email_to, message.as_string())
        logger.info("Email sent successfully via Gmail SMTP!")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail SMTP authentication failed. Check credentials.")
        return False
    except Exception as e:
        logger.error("An error occurred while sending email via Gmail SMTP: %s", e)
        return False
