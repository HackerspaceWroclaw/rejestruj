#!/usr/bin/python

import re
import random
import crypt
import ldap

#-----------------------------------------------------------------------------

class RegisterError(Exception):
    def __init__(self, message, errors = None):
        super(RegisterError, self).__init__(message)
        if errors is None:
            self.errors = {}
        else:
            self.errors = errors

#-----------------------------------------------------------------------------

def register(config, nick, email, firstname, lastname, password):
    validate(nick, email, firstname, lastname)
    values = {
        "nick":      nick,
        "email":     email,
        "firstname": firstname,
        "lastname":  lastname,
        "password":  password,
        "crypt_password": passwd(password),
    }
    (dn, attrs) = fill(config, values)
    print ldif(dn, attrs)

def validate(nick, email, firstname, lastname):
    # TODO: raise RegisterError on problem
    pass

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

def ldif(dn, attrs):
    body = []
    for name in sorted(attrs):
        for value in attrs[name]:
            body.append("%s: %s" % (name, value))
    return "dn: %s\n%s\n" % (dn, "\n".join(body))

#-----------------------------------------------------------------------------

def ldap_add(config, dn, attrs):
    conn = ldap.initialize(config['LDAP_URI'])
    conn.protocol_version = ldap.VERSION3
    # FIXME: catch ldap.LDAPError
    conn.bind_s(config['LDAP_BIND_DN'], config['LDAP_BIND_PW'],
                ldap.AUTH_SIMPLE)
    # FIXME: catch ldap.ALREADY_EXISTS
    try:
        conn.add_s(dn, attrs.items())
    except ldap.ALREADY_EXISTS:
        raise RegisterError(
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
