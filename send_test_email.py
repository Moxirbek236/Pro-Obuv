import os
import smtplib
import ssl
from email.message import EmailMessage

smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.environ.get('SMTP_PORT', '465'))
smtp_user = os.environ.get('SMTP_USER')
smtp_pass = os.environ.get('SMTP_PASS')
smtp_from = os.environ.get('SMTP_FROM') or smtp_user

to_addr = os.environ.get('TEST_TO', smtp_user)

msg = EmailMessage()
msg['From'] = smtp_from
msg['To'] = to_addr
msg['Subject'] = 'Test email from send_test_email.py'
msg.set_content('This is a test message from send_test_email.py')

try:
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        server.set_debuglevel(1)
        if getattr(server, 'sock', None):
            server.sock.settimeout(15)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        server.set_debuglevel(1)
        if getattr(server, 'sock', None):
            server.sock.settimeout(15)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        if getattr(server, 'sock', None):
            server.sock.settimeout(15)
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    print('Email send attempted successfully')
except Exception as e:
    print('Email send failed:', e)
