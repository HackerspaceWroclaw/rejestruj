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

SESSION_VARIABLE = 'hswro_rejestruj'

#-----------------------------------------------------------------------------

EMAIL_FROM = 'noreply@hswro.org'

SMTP_HOST = 'localhost'
SMTP_PORT = 25
SMTP_ENCRYPTION = None      # None | "SSL" | "STARTTLS"
SMTP_CREDENTIALS = None     # None | (user, password)

#-----------------------------------------------------------------------------

# NOTE: if your XML-RPC interface to Mailman is covered by HTTP
# authentication, you need to encode this fact in the URL
MAILMAN_XMLRPC_URL = None
#MAILMAN_XMLRPC_URL = 'https://localhost:3033/'
#MAILMAN_XMLRPC_URL = 'https://rejestruj:<password>@localhost:3033/'

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
    "userPassword": "%(crypt_password)s",
    "contactMail": "%(email)s",
    "objectClass": ["top", "hSWroUser"],
    "isHSWroMember": False,
    "isVerified": False,
}

#-----------------------------------------------------------------------------

try:
    from settings_local import *
except ImportError:
    pass

#-----------------------------------------------------------------------------

SECRET_KEY_FILE_ABS = os.path.join(APP_ROOT, SECRET_KEY_FILE)
SECRET_KEY = open(SECRET_KEY_FILE_ABS).readline().strip()

DATABASE_FILE_ABS = os.path.join(APP_ROOT, DATABASE_FILE)

#-----------------------------------------------------------------------------
# vim:ft=python
