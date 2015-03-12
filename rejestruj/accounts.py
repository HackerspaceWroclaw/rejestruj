#!/usr/bin/python
# -*- coding: utf-8 -*-

import fdb
import fldap

import os
import base64
import re
import copy

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

class UserExistsError(Exception):
    pass

class NoSuchUserError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class InvalidTokenError(Exception):
    pass

#-----------------------------------------------------------------------------

class NewAccount:
    def __init__(self, config, token = None):
        self.config = config
        self.db = fdb.DB(self.config)
        self.token = token
        if self.token is None:
            # blank user for registration
            self.nick      = None
            self.email     = None
            self.firstname = None
            self.lastname  = None
            self.password  = None
            self.crypt_password = None
        else:
            # load from fdb.DB for registration
            result = self.db.load_form(self.token)
            if result is None:
                raise InvalidTokenError()
            self.nick      = result[0]
            self.email     = result[1]
            self.firstname = result[2]
            self.lastname  = result[3]
            self.password  = None
            self.crypt_password = result[4]

    def store_for_activation(self):
        self._validate() # raises RegisterError in case of error
        if self.password is not None:
            self.crypt_password = fldap.passwd(self.password)

        token = generate_token()
        self.db.save_form(
            token = token,
            nick      = self.nick,
            email     = self.email,
            firstname = self.firstname,
            lastname  = self.lastname,
            password  = self.crypt_password,
        )
        return token

    def register(self):
        self._validate() # again, but this should not be necessary
        ldap = fldap.LDAP(self.config)
        # delete forms after successful LDAP connection
        self.db.delete_all_forms_for(self.nick)
        try:
            ldap.add_user(
                nick      = self.nick,
                email     = self.email,
                firstname = self.firstname,
                lastname  = self.lastname,
                crypt_password = self.crypt_password,
            )
        except fldap.LDAPError:
            # account already exists
            raise UserExistsError()

    def _validate(self):
        # FIXME: tight coupling with registration form
        errors = {}
        if self.nick in (None, ""):
            errors["nick"] = u"nick jest pusty"
        elif not _NICK_RE.match(self.nick):
            errors["nick"] = u"niedozwolone znaki w nicku"

        if self.email in (None, ""):
            errors["email"] = u"e-mail jest pusty"
        elif not _EMAIL_RE.match(self.email):
            errors["email"] = u"e-mail ma nieprawidłową formę"

        if self.firstname in (None, ""):
            errors["firstname"] = u"imię jest puste"

        if self.lastname in (None, ""):
            errors["lastname"] = u"nazwisko jest puste"

        if len(errors) > 0:
            raise RegisterError(u"błędy w formularzu", errors)

#-----------------------------------------------------------------------------

class Account:
    def __init__(self, config, username = None, password = None,
                 reset_password = None, change_email = None):
        self.config = config
        self.ldap = fldap.LDAP(self.config)
        self.db = None
        self.reset_password_token = reset_password
        self.change_email_token = change_email
        #self.attrs = {...}
        #self.old_attrs = {...}
        #self.dn = "..."

        if self.reset_password_token is not None:
            # password reset confirmation
            self.db = fdb.DB(self.config)
            username = self.db.load_reset_password_token(self.reset_password_token)
            if username is None:
                raise InvalidTokenError()
        elif self.change_email_token is not None:
            # e-mail change confirmation
            # XXX: old e-mail will be stored in self.old_attrs, while the
            # requested (new) one will be put in self.attrs
            self.db = fdb.DB(self.config)
            (username, new_email) = \
                self.db.load_email_change_token(self.change_email_token)
            if username is None:
                raise InvalidTokenError()

        # either simple loading user's attributes or authentication attempt
        result = self.ldap.find(username)
        if result is None and password is None:
            raise NoSuchUserError()
        if result is None and password is not None:
            raise AuthenticationError()

        self.dn = result[0]
        self.attrs = result[1]
        if password is not None and not self.ldap.bind(self.dn, password):
            raise AuthenticationError()

        self.old_attrs = copy.deepcopy(self.attrs)
        if self.change_email_token is not None:
            # make sure it will compare correctly to
            # self.old_fields['contactMail']
            self.attrs['contactMail'] = [fldap.make_str(new_email)]

    #-------------------------------------------------------
    # dict-like interface {{{

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def __delitem__(self, key):
        if key in self.attrs:
            del self.attrs[key]

    def __getitem__(self, key):
        return self.attrs.get(key)

    def field(self, key, default = None):
        return self.attrs.get(key, default)

    def old_field(self, key, default = None):
        return self.old_attrs.get(key, default)

    def __contains__(self, key):
        return key in self.attrs

    def __len__(self):
        return len(self.attrs)

    # }}}
    #-------------------------------------------------------

    def save(self):
        changes = {}
        for a in self.attrs:
            if type(self.attrs[a]) == unicode:
                # so it compares to str correctly
                self.attrs[a] = fldap.make_str(self.attrs[a])
            if a not in self.old_attrs or self.attrs[a] != self.old_attrs[a]:
                changes[a] = self.attrs[a]
        self.ldap.update(dn = self['dn'], **changes)
        # TODO: check contactMail and uid and raise RegisterError

    def request_email_change(self, new_email):
        if self.db is None:
            self.db = fdb.DB(self.config)
        token = generate_token()
        self.db.save_email_change_token(token, self['uid'], new_email)
        return token

    def clear_email_change_request(self):
        self.db.delete_email_change_token(self.change_email_token)

    def request_reset_password(self):
        if self.db is None:
            self.db = fdb.DB(self.config)
        token = generate_token()
        self.db.save_reset_password_token(token, self['uid'])
        return token

    def clear_reset_password_request(self):
        self.db.delete_reset_password_token(self.reset_password_token)

    def set_password(self, password):
        self.ldap.set_password(dn = self['dn'], password = password)

    #-------------------------------------------------------

#-----------------------------------------------------------------------------

def generate_token():
    return base64.b64encode(os.urandom(30))

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
