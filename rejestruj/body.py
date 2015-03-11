#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
import rejestruj.settings
import accounts
import sessions
import mailman
import fsmtp

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

#-----------------------------------------------------------------------------

@app.route("/register", methods = ["POST"])
def register():
    password = flask.request.values.get("password", "")
    password2 = flask.request.values.get("password_repeated", "")

    if password == "" or password != password2:
        errors = {
            "password": u"hasła się nie zgadzają",
        }
        return flask.render_template('register.html', errors = errors)

    try:
        account = accounts.NewAccount(app.config)
        account.nick      = flask.request.values['nick']
        account.email     = flask.request.values['email']
        account.firstname = flask.request.values['firstname']
        account.lastname  = flask.request.values['lastname']
        account.password  = password
        activation_token = account.store_for_activation()
    except accounts.RegisterError, e:
        return flask.render_template('register.html', errors = e.errors)

    url = flask.url_for('confirm', token = activation_token, _external = True)
    values = {
        'activation_link': url,
        'nick': account.nick,
        'email_from': app.config['EMAIL_FROM'],
        'email_to': account.email,
    }
    email_body = flask.render_template('email_confirm.txt', **values)

    smtp = fsmtp.SMTP(app.config)
    smtp.send_email(account.email, email_body)

    title = u"Zarejestrowano"
    message = u"E-mail aktywacyjny został wysłany."
    return flask.render_template('message.html', message = message,
                                 title = title)

#-----------------------------------------------------------------------------

@app.route("/confirm/<path:token>")
def confirm(token):
    try:
        account = accounts.NewAccount(app.config, token = token)
        account.register()
    except accounts.InvalidTokenError:
        title = u"Rejestracja nieudana"
        message = u"Nieprawidłowy link aktywacyjny."
        return flask.render_template('message.html', message = message,
                                     title = title, error = True)
    except accounts.UserExistsError:
        title = u"Rejestracja nieudana"
        message = u"Użytkownik %s już istnieje" % (account.nick,)
        return flask.render_template('message.html', message = message,
                                     title = title, error = True)

    title = u"Zarejestrowano"
    message = u"Użytkownik utworzony."
    link = {
        'url': flask.url_for('index'),
        'description': u'Zaloguj',
    }
    return flask.render_template('message.html', message = message,
                                 title = title, link = link)

#-----------------------------------------------------------------------------

@app.route("/login", methods = ["POST"])
def login():
    if 'reset_password' in flask.request.values:
        # TODO: catch NoSuchUserException
        account = accounts.Account(app.config, flask.request.values['nick'])
        token = account.request_reset_password()
        url = flask.url_for('reset_password', token = token, _external = True)
        values = {
            'reset_password_link': url,
            'nick': account['uid'],
            'email_from': app.config['EMAIL_FROM'],
            'email_to': account['contactMail'][0],
        }
        email_body = flask.render_template('email_reset_password.txt', **values)

        smtp = fsmtp.SMTP(app.config)
        smtp.send_email(account['contactMail'][0], email_body)

        title = u"Resetowanie hasła"
        message = u"E-mail dla resetowania hasła został wysłany."
        link = {
            'url': flask.url_for('index'),
            'description': u'Powrót do logowania',
        }
        return flask.render_template('message.html', message = message,
                                     title = title)

    try:
        username = flask.request.values['nick']
        password = flask.request.values.get('password')
        account = accounts.Account(app.config, username, password)
    except accounts.AuthenticationError:
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
    session['member'] = account.field('isHSWroMember', False)
    session['verified'] = account.field('isVerified', False)
    session['email'] = account.field('contactMail', [None])[0]
    session['hs_emails'] = account.field('mail', [])
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
    session = sessions.Session(app.config)
    maillists = mailman.MailLists(
        app.config, email = session['email'], hsmember = session['member'],
    )
    return flask.render_template('panel.html', account = session,
                                 maillists = maillists)

#-----------------------------------------------------------------------------

@app.route("/panel/update", methods = ["GET", "POST"])
def account_update(*args, **kwargs):
    if flask.request.method == "GET":
        # stale link in browser
        return flask.redirect(flask.url_for('panel'))
    # flask.request.method == "POST"
    return _account_update(*args, **kwargs)

@require_login
def _account_update():
    session = sessions.Session(app.config)
    account = accounts.Account(app.config, session['user'])

    # NOTE: ldap_update() calls in this manner would be highly ineffective,
    # but fortunately HTML forms send these fields one at a request, so it's
    # generally OK

    full_name = flask.request.values.get("full_name", "")
    if full_name != "":
        session['full_name'] = account['cn'] = full_name

    email = flask.request.values.get("email", "")
    if email != "":
        session['email'] = account['contactMail'] = [email]

    password = flask.request.values.get("password", "")
    password2 = flask.request.values.get("password_repeated", "")
    if password != "" or password2 != "":
        if password != password2:
            message = u'Hasła się nie zgadzają.'
            title = u'Błąd ustawiania hasła'
            link = {
                'url': flask.url_for('panel'),
                'description': u'Powrót',
            }
            return flask.render_template('message.html', message = message,
                                         title = title, link = link)
        account.set_password(password)

    account.save()
    session.save()

    # TODO: some message maybe?
    return flask.redirect(flask.url_for('panel'))

#-----------------------------------------------------------------------------

@app.route("/panel/subscribe", methods = ["GET", "POST"])
def subscribe(*args, **kwargs):
    if flask.request.method == "GET":
        # stale link in browser
        return flask.redirect(flask.url_for('panel'))
    # flask.request.method == "POST"
    return _subscribe(*args, **kwargs)

@require_login
def _subscribe():
    return flask.redirect(flask.url_for('panel'))

#-----------------------------------------------------------------------------

@app.route("/reset_password/<path:token>", methods = ["GET", "POST"])
def reset_password(token):
    try:
        account = accounts.Account(app.config, token = token)
    except accounts.InvalidTokenError:
        title = u"Resetowanie hasła nieudane"
        message = u"Nieprawidłowy link do resetowania hasła."
        return flask.render_template('message.html', message = message,
                                     title = title)
    except accounts.NoSuchUserError:
        title = u"Resetowanie hasła nieudane"
        message = u"Użytkownik nie istnieje."
        return flask.render_template('message.html', message = message,
                                     title = title)

    password = flask.request.values.get("password", "")
    password2 = flask.request.values.get("password_repeated", "")
    if flask.request.method == "POST" and (password != "" or password2 != ""):
        if password != password2:
            message = u"Hasła się nie zgadzają"
            return flask.render_template('reset_password.html',
                                         nick = account['uid'], token = token,
                                         message = message)

        account.set_password(password)
        account.save()
        account.clear_reset_password_request()

        title = u"Resetowanie hasła udane"
        message = u"Hasło zresetowane."
        link = {
            'url': flask.url_for('index'),
            'description': u'Zaloguj',
        }
        return flask.render_template('message.html', message = message,
                                     title = title, link = link)

    return flask.render_template('reset_password.html', nick = account['uid'],
                                 token = token)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
