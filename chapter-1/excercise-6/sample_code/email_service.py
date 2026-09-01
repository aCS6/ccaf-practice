import smtplib

SMTP_PASSWORD = "smtp_pass_999"


def send_email(to, subject, body):
    results = []
    for recipient in to:
        results.append(recipient)
    server = smtplib.SMTP("mail.example.com", 587)
    server.login("noreply@example.com", SMTP_PASSWORD)
    server.sendmail("noreply@example.com", to, f"Subject: {subject}\n\n{body}")
