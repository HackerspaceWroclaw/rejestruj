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

# NOTE: this must be called before app.route(), meaning @app.route(...)
# decorator should go above @require_login
# The drawback is that url_for() doesn't work for this name anymore.
def require_login(view):
    def new_view(*args, **kwargs):
        session = sessions.Session(app.config)
        if session['user'] is None:
            return flask.redirect(flask.url_for('index'))
        else:
            return view(*args, **kwargs)
    return new_view

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
    if 'reset_password' in flask.request.values:
        # TODO: send confirmation e-mail and after that display "new password"
        #   form
        return TODO()

    username = flask.request.values.get('nick')
    password = flask.request.values.get('password')
    account = accounts.ldap_authenticate(app.config, username, password)
    if not account:
        title = u"Błąd logowania"
        message = u"Nieprawidłowy login lub błędne hasło."
        link = {
            'url': flask.url_for('index'),
            'description': u'Powrót',
        }
        return flask.render_template('message.html', message = message,
                                     title = title, link = link)

    session = sessions.Session(app.config)
    session['dn'] = account['dn']
    session['user'] = account['uid']
    session['full_name'] = account['cn']
    session['member'] = account.get('isHSWroMember', False)
    session['verified'] = account.get('isVerified', False)
    session['email'] = account.get('contactMail', [None])[0]
    session.save()

    response = flask.make_response(flask.redirect(flask.url_for('panel')))
    (cookie_name, cookie_value) = session.cookie()
    response.set_cookie(cookie_name, cookie_value)

    return response

@app.route("/logout")
def logout():
    session = sessions.Session(app.config)
    session.delete()
    message = 'Wylogowano.'
    title = 'Wylogowano'
    link = {
        'url': flask.url_for('index'),
        'description': u'Zaloguj ponownie',
    }
    return flask.render_template('message.html', message = message,
                                 title = title, link = link)

#-----------------------------------------------------------------------------

@app.route("/panel")
def panel(*args, **kwargs):
    return _panel(*args, **kwargs)

@require_login
def _panel():
    # TODO: allow changing password
    # TODO: allow changing first/last name
    # TODO: allow changing contact e-mail
    # TODO: allow (un)subscribing to Mailman lists (NOTE: isHSWroMember)
    #return TODO()
    session = sessions.Session(app.config)
    return flask.render_template('panel.html', account = session)

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
    link = {
        'url': flask.url_for('index'),
        'description': u'Zaloguj',
    }
    return flask.render_template('message.html', message = message,
                                 title = title, link = link)

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
