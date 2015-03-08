#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
import rejestruj.settings
import accounts
import sessions
import db
import os
import base64

#-----------------------------------------------------------------------------

app = flask.Flask(__name__)
app.config.from_object(rejestruj.settings)

#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return flask.render_template('index.html')

@app.route("/register", methods = ["POST"])
def register():
    password = flask.request.values.get('password')
    password2 = flask.request.values.get('password_repeated')

    if password in ["", None] or password != password2:
        errors = {
            "password": "hasła się nie zgadzają",
        }
        return flask.render_template('register.html', errors = errors)

    try:
        nick      = flask.request.values['nick']
        email     = flask.request.values['email']
        firstname = flask.request.values['firstname']
        lastname  = flask.request.values['lastname']
        accounts.validate(config = app.config, nick = nick, email = email,
                          firstname = firstname, lastname = lastname)
    except accounts.RegisterError, e:
        return flask.render_template('register.html', errors = e.errors)

    dbconn = db.connection(app.config)
    token = generate_token(app.config)
    accounts.send_activation_email(app.config, email, token, nick)
    db.save_form(
        dbconn = dbconn,
        token  = token,
        nick      = nick,
        email     = email,
        firstname = firstname,
        lastname  = lastname,
        password  = password,
    )

    title = u"Zarejestrowano"
    message = u"E-mail aktywacyjny został wysłany."
    return flask.render_template('message.html', message = message,
                                 title = title)

#-----------------------------------------------------------------------------

@app.route("/login", methods = ["POST"])
def login():
    # TODO: try logging in with LDAP, then establish a session and redirect
    # TODO: on reset password, send confirmation e-mail and after that display
    #   "new password" form
    return TODO()

@app.route("/logout")
def logout():
    # TODO: delete HTTP session
    return TODO()

#-----------------------------------------------------------------------------

@app.route("/panel")
def panel():
    # TODO: allow changing password
    # TODO: allow changing first/last name
    # TODO: allow changing contact e-mail
    # TODO: allow (un)subscribing to Mailman lists (NOTE: isHSWroMember)
    #return TODO()
    return flask.render_template('panel.html')

#-----------------------------------------------------------------------------

@app.route("/confirm/<path:token>")
def confirm(token):
    dbconn = db.connection(app.config)
    form_data = db.load_form(dbconn, token)
    if form_data is None:
        title = u"Rejestracja nieudana"
        message = u"Nieprawidłowy link aktywacyjny."
        return flask.render_template('message.html', message = message,
                                     title = title, error = True)

    (nick, email, firstname, lastname, crypt_password) = form_data

    accounts.register(
        config = app.config, nick = nick, email = email,
        crypt_password = crypt_password,
        firstname = firstname, lastname = lastname,
    )
    title = u"Zarejestrowano"
    message = u"Użytkownik utworzony."
    return flask.render_template('message.html', message = message,
                                 title = title)

#-----------------------------------------------------------------------------

def TODO():
    message = u'Ta strona jeszcze nie jest zrobiona.'
    title = u'TODO'
    return flask.render_template('message.html', message = message,
                                 title = title, error = True)

def generate_token(config):
    return base64.b64encode(os.urandom(30))

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
