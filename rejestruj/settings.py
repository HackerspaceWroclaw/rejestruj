#!/usr/bin/python
#
# Default settings for rejestruj webapplication.
#
#-----------------------------------------------------------------------------

import os

#-----------------------------------------------------------------------------

APP_ROOT = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY_FILE = 'secret.txt'

DEBUG = True

#-----------------------------------------------------------------------------

EMAIL_FROM = 'noreply@hswro.org'

SMTP_HOST = 'localhost'
SMTP_PORT = 25
SMTP_ENCRYPTION = None      # None | "SSL" | "STARTTLS"
SMTP_CREDENTIALS = None     # None | (user, password)

#-----------------------------------------------------------------------------

# SQLite3
DATABASE_FILE = 'db/rejestruj.db'

#-----------------------------------------------------------------------------

LDAP_URI = "ldapi:///"
LDAP_BIND_DN = "cn=root,dc=hswro.org"
LDAP_BIND_PW = "<some password>"

LDAP_USER_TREE = "dc=hswro.org"
LDAP_USER_DN_TEMPLATE = "uid=%(nick)s,ou=HS members,dc=hswro.org"
LDAP_USER_TEMPLATE = {
    "uid": "%(nick)s",
    "cn": "%(firstname)s %(lastname)s",
    "userPassword": "{CRYPT}%(crypt_password)s",
    "contactMail": "%(email)s",
    "objectClass": ["top", "hSWroUser"],
    "isHSWroMember": False,
    "isVerified": False,
}

#-----------------------------------------------------------------------------

SECRET_KEY_FILE_ABS = os.path.join(APP_ROOT, SECRET_KEY_FILE)
SECRET_KEY = open(SECRET_KEY_FILE_ABS).readline().strip()

DATABASE_FILE_ABS = os.path.join(APP_ROOT, DATABASE_FILE)

#-----------------------------------------------------------------------------
# vim:ft=python
