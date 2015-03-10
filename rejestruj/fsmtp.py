#!/usr/bin/python

import smtplib
import flask

#-----------------------------------------------------------------------------

class SMTP:
    def __init__(self, config):
        self.envelope_sender = config['EMAIL_FROM']

        if config['SMTP_ENCRYPTION'] is None:
            self.smtp = smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT'])
        elif config['SMTP_ENCRYPTION'] == "STARTTLS":
            self.smtp = smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT'])
            self.smtp.starttls()
        elif config['SMTP_ENCRYPTION'] == "SSL":
            self.smtp = smtplib.SMTP_SSL(config['SMTP_HOST'], config['SMTP_PORT'])

        if config['SMTP_CREDENTIALS'] is not None:
            (user, passwd) = config['SMTP_CREDENTIALS']
            self.smtp.login(user, passwd)

    def __del__(self):
        self.smtp.quit()

    def send_email(self, recipient, email_body):
        if not email_body.endswith("\n"):
            email_body += "\n"

        self.smtp.sendmail(self.envelope_sender, recipient,
                           email_body.encode('utf-8'))

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
