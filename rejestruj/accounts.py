#!/usr/bin/python

import re
import random
import crypt
import ldap
import flask
import smtplib

#-----------------------------------------------------------------------------

class RegisterError(Exception):
    def __init__(self, message, errors = None):
        super(RegisterError, self).__init__(message)
        if errors is None:
            self.errors = {}
        else:
            self.errors = errors

#-----------------------------------------------------------------------------

def register(config, nick, email, firstname, lastname, crypt_password):
    values = {
        "nick":      nick,
        "email":     email,
        "firstname": firstname,
        "lastname":  lastname,
        "crypt_password": crypt_password,
    }
    (dn, attrs) = fill(config, values)
    ldap_add(config, dn, attrs)

def validate(nick, email, firstname, lastname):
    # TODO: raise RegisterError on problem
    pass

#-----------------------------------------------------------------------------

def send_activation_email(config, email, token, nick):
    url = flask.url_for('confirm', token = token, _external = True)
    email_body = flask.render_template(
        'email.txt',
        nick = nick, activation_link = url,
        email_from = config['EMAIL_FROM'], email_to = email,
    )
    if not email_body.endswith("\n"):
        email_body += "\n"

    if config['SMTP_ENCRYPTION'] is None:
        smtp = smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT'])
    elif config['SMTP_ENCRYPTION'] == "STARTTLS":
        smtp = smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT'])
        smtp.starttls()
    elif config['SMTP_ENCRYPTION'] == "SSL":
        smtp = smtplib.SMTP_SSL(config['SMTP_HOST'], config['SMTP_PORT'])

    if config['SMTP_CREDENTIALS'] is not None:
        (user, passwd) = config['SMTP_CREDENTIALS']
        smtp.login(user, passwd)

    smtp.sendmail(config['EMAIL_FROM'], email, email_body)
    smtp.quit()

#-----------------------------------------------------------------------------

def make_str(value):
    if type(value) == str:
        return value
    if type(value) == unicode:
        return value.encode('utf-8')

def fill(config, fill_values):
    dn = config['LDAP_USER_DN_TEMPLATE'] % fill_values
    attrs = {}
    for name in config['LDAP_USER_TEMPLATE']:
        value = config['LDAP_USER_TEMPLATE'][name]
        if type(value) in (list, tuple):
            attrs[name] = [make_str(v % fill_values) for v in value]
        elif type(value) in (str, unicode):
            attrs[name] = [make_str(value % fill_values)]
        elif type(value) == bool:
            attrs[name] = ["TRUE" if value else "FALSE"]
        else:
            attrs[name] = [str(value)]
    return (dn, attrs)

#-----------------------------------------------------------------------------

def ldap_add(config, dn, attrs):
    conn = ldap.initialize(config['LDAP_URI'])
    conn.protocol_version = ldap.VERSION3
    # FIXME: catch ldap.LDAPError
    conn.bind_s(config['LDAP_BIND_DN'], config['LDAP_BIND_PW'],
                ldap.AUTH_SIMPLE)
    try:
        conn.add_s(dn, attrs.items())
    except ldap.ALREADY_EXISTS:
        # this typically shouldn't happen
        raise RegisterError("specified username already exists")
    conn.unbind_s()

#-----------------------------------------------------------------------------

# MD5-style password
def passwd(password):
    salt_space = "abcdefghijklmnopqrstuvwxyz" \
                 "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                 "0123456789./"
    salt = "$1$%s$" % "".join([
        salt_space[random.randrange(0, 64)]
        for i in xrange(16)
    ])
    return crypt.crypt(password, salt)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
