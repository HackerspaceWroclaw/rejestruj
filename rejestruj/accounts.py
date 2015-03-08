#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import random
import crypt
import ldap
import ldap.filter
import flask
import smtplib

#-----------------------------------------------------------------------------

_NICK_RE = re.compile(r'^[a-zA-Z0-9_.-]+$')
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$')

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

def validate(config, nick, email, firstname, lastname):
    errors = {}
    if nick in (None, ""):
        errors["nick"] = u"nick jest pusty"
    elif not _NICK_RE.match(nick):
        errors["nick"] = u"niedozwolone znaki w nicku"
    elif ldap_exists(config, nick):
        errors["nick"] = u"użytkownik już istnieje"

    if email in (None, ""):
        errors["email"] = u"e-mail jest pusty"
    elif not _EMAIL_RE.match(email):
        errors["email"] = u"e-mail ma nieprawidłową formę"

    if firstname in (None, ""):
        errors["firstname"] = u"imię jest puste"

    if lastname in (None, ""):
        errors["lastname"] = u"nazwisko jest puste"

    if len(errors) > 0:
        raise RegisterError(u"błędy w formularzu", errors)

#-----------------------------------------------------------------------------

def send_email(config, sender, recipient, email_template, template_values):
    email_body = flask.render_template(email_template, **template_values)
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

    smtp.sendmail(sender, recipient, email_body.encode('utf-8'))
    smtp.quit()

def send_activation_email(config, email, token, nick):
    email_template = 'email_confirm.txt'
    values = {
        'activation_link': flask.url_for('confirm', token = token, _external = True),
        'nick': nick,
        'email_from': config['EMAIL_FROM'],
        'email_to': email,
    }
    send_email(config, config['EMAIL_FROM'], email, email_template, values)

def send_reset_password_email(config, token, nick):
    conn = ldap_connect(config)
    (dn, node) = ldap_find(config, conn, nick, ['contactMail'])
    conn.unbind_s()
    if node is None:
        return
    email = node['contactMail']
    email_template = 'email_reset_password.txt'
    values = {
        'confirmation_link': flask.url_for('reset_password_confirm',
                                           token = token, _external = True),
        'nick': nick,
        'email_from': config['EMAIL_FROM'],
        'email_to': email,
    }
    send_email(config, config['EMAIL_FROM'], email, email_template, values)

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

def ldap_connect(config):
    conn = ldap.initialize(config['LDAP_URI'])
    conn.protocol_version = ldap.VERSION3
    # FIXME: catch ldap.LDAPError
    conn.bind_s(config['LDAP_BIND_DN'], config['LDAP_BIND_PW'],
                ldap.AUTH_SIMPLE)
    return conn

def ldap_add(config, dn, attrs):
    conn = ldap_connect(config)
    try:
        conn.add_s(dn, attrs.items())
    except ldap.ALREADY_EXISTS:
        # this typically shouldn't happen
        raise RegisterError("specified username already exists")
    conn.unbind_s()

def ldap_exists(config, nick):
    conn = ldap_connect(config)
    user_filter = ldap.filter.filter_format('uid=%s', [nick])
    result = conn.search_s(config['LDAP_USER_TREE'], ldap.SCOPE_SUBTREE,
                           user_filter, attrlist = ['uid'])
    conn.unbind_s()
    return (len(result) > 0)

def ldap_update(config, dn, **attrs):
    conn = ldap_connect(config)
    operations = [
        (ldap.MOD_REPLACE, name, [make_str(attrs[name])])
        for name in attrs
    ]
    conn.modify_s(dn, operations)
    conn.unbind_s()

def ldap_set_password(config, dn, new_password):
    # TODO: better way of changing passwords (e.g. not hardcoded to
    # userPassword attribute and CRYPT hash)
    password_field = "{CRYPT}%s" % (passwd(new_password),)
    ldap_update(config, dn, userPassword = password_field)

def ldap_find(config, conn, username, attrs = None):
    if attrs is None:
        attrs = ['uid', 'cn', 'contactMail', 'isHSWroMember', 'isVerified']

    user_filter = ldap.filter.filter_format('uid=%s', [username])
    result = conn.search_s(config['LDAP_USER_TREE'], ldap.SCOPE_SUBTREE,
                           user_filter, attrlist = attrs)
    if len(result) == 0:
        return (None, None)
    (user_dn, user_node) = result[0] # TODO: what with multiple hits?
    # XXX: assume commonName is single-valued (which is untrue, according to
    # LDAP schema)
    for a in ['uid', 'cn']:
        if a in user_node:
            user_node[a] = user_node[a][0]
    for a in ['isHSWroMember', 'isVerified']:
        if a in user_node:
            # "TRUE" | "FALSE"
            user_node[a] = (user_node[a][0] == "TRUE")
    user_node['dn'] = user_dn
    return (user_dn, user_node)

def ldap_authenticate(config, username, password):
    conn = ldap_connect(config)
    (user_dn, user_node) = ldap_find(config, conn, username)

    if user_dn is None:
        conn.unbind_s()
        return None

    try:
        conn.bind_s(user_dn, password)
        authenticated = True
    except ldap.LDAPError:
        authenticated = False
    conn.unbind_s()

    if authenticated:
        return user_node
    else:
        return None

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
