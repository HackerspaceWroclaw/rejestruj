#!/usr/bin/python

import ldap
import ldap.filter
import crypt
import random

#-----------------------------------------------------------------------------

class LDAPError(Exception):
    pass

#-----------------------------------------------------------------------------

class LDAP:
    def __init__(self, config):
        self.config = config
        self.user_tree = config['LDAP_USER_TREE']
        self.conn = ldap.initialize(config['LDAP_URI'])
        self.conn.protocol_version = ldap.VERSION3
        self.bind()

    #-------------------------------------------------------
    # authentication {{{

    def bind(self, bind_dn = None, bind_pw = None):
        if bind_dn is None and bind_pw is None:
            bind_dn = self.config['LDAP_BIND_DN']
            bind_pw = self.config['LDAP_BIND_PW']
        try:
            self.conn.bind_s(bind_dn, bind_pw, ldap.AUTH_SIMPLE)
            return True
        except ldap.LDAPError:
            # hope it's authentication error
            return False

    def authenticate(self, user, password):
        result = self.find(user)
        if result is None:
            return None
        (bind_dn, user_attrs) = result[0]
        if self.bind(bind_dn, password):
            # TODO: rebind back to LDAP_BIND_DN?
            return user_attrs
        else:
            return None

    # }}}
    #-------------------------------------------------------
    # adding entries {{{

    def add_user(self, **values):
        dn = self.config['LDAP_USER_DN_TEMPLATE'] % values
        attrs = {}
        for name, value in self.config['LDAP_USER_TEMPLATE'].iteritems():
            if type(value) in (list, tuple):
                attrs[name] = [v % values for v in value]
            elif type(value) in (str, unicode):
                attrs[name] = value % values
            else:
                attrs[name] = value
        self.add(dn, attrs)
        return (dn, attrs)

    def add(self, dn, attrs):
        ldap_attrs = []
        for (name, value) in attrs.iteritems():
            if type(value) in (list, tuple):
                ldap_attrs.append((name, [make_str(v) for v in value]))
            elif type(value) in (str, unicode):
                ldap_attrs.append((name, [make_str(value)]))
            elif type(value) == bool:
                ldap_attrs.append((name, ["TRUE" if value else "FALSE"]))
            else: # integers?
                ldap_attrs.append((name, [str(value)]))
        try:
            self.conn.add_s(dn, ldap_attrs)
        except ldap.ALREADY_EXISTS:
            # this typically shouldn't happen
            raise LDAPError("entry %s already exists" % (dn,))

    # }}}
    #-------------------------------------------------------
    # account lookup {{{

    def exists(self, username):
        user_filter = ldap.filter.filter_format('uid=%s', [username])
        result = conn.search_s(self.user_tree, ldap.SCOPE_SUBTREE,
                               user_filter, attrlist = ['uid'])
        return (len(result) > 0)

    def find(self, username, attrs = None):
        if attrs is None:
            attrs = [
                'uid', 'cn', 'contactMail', 'mail',
                'isHSWroMember', 'isVerified',
            ]

        user_filter = ldap.filter.filter_format('uid=%s', [username])
        result = self.conn.search_s(self.user_tree, ldap.SCOPE_SUBTREE,
                                    user_filter, attrlist = attrs)
        if len(result) == 0:
            return None

        (user_dn, user_attrs) = result[0] # TODO: what with multiple hits?
        # XXX: assume commonName is single-valued (which is untrue, according
        # to LDAP schema)
        for a in ['uid', 'cn']:
            if a in user_attrs:
                user_attrs[a] = user_attrs[a][0]
        for a in ['isHSWroMember', 'isVerified']:
            if a in user_attrs:
                # "TRUE" | "FALSE"
                user_attrs[a] = (user_attrs[a][0] == "TRUE")
        user_attrs['dn'] = user_dn
        return (user_dn, user_attrs)

    # }}}
    #-------------------------------------------------------
    # updating fields {{{

    def update(self, dn, **attrs):
        operations = [
            (ldap.MOD_REPLACE, name, [make_str(attrs[name])])
            for name in attrs
        ]
        self.conn.modify_s(dn, operations)

    def set_password(self, user = None, dn = None, password = None):
        if password is None:
            # can't have DN/user before password and require the latter to be
            # not None in args list
            raise ValueError("password argument must be set")
        if dn is None and user is None:
            raise LDAPError("either username or DN must be set")
        if dn is None:
            result = self.find(user, ['uid'])
            if result is None:
                raise LDAPError("user %s doesn't exist" % (user,))
            dn = result[0]

        # TODO: better way of changing passwords (e.g. not hardcoded to
        # userPassword attribute and CRYPT hash)
        password_field = passwd(password)
        self.update(dn, userPassword = password_field)

    # }}}
    #-------------------------------------------------------

#-----------------------------------------------------------------------------

def make_str(value):
    if type(value) == str:
        return value
    if type(value) == unicode:
        return value.encode('utf-8')

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
    return "{CRYPT}%s" % (crypt.crypt(password, salt),)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
