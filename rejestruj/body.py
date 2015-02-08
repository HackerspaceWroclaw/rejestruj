#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
import rejestruj.settings
import accounts

#-----------------------------------------------------------------------------

app = flask.Flask(__name__)
app.config.from_object(rejestruj.settings)

#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return flask.render_template('index.html')

@app.route("/register", methods = ["GET"])
def register_form():
    return flask.render_template('register.html')

@app.route("/register", methods = ["POST"])
def register():
    passwd = flask.request.values.get('password')
    passwd2 = flask.request.values.get('password_repeated')

    if passwd in ["", None] or passwd != passwd2:
        errors = {
            "password": "hasła się nie zgadzają",
        }
        return flask.render_template('register.html', errors = errors)

    try:
        accounts.register(
            config = app.config,
            nick      = flask.request.values['nick'],
            email     = flask.request.values['email'],
            firstname = flask.request.values['firstname'],
            lastname  = flask.request.values['lastname'],
            password  = flask.request.values['password'],
        )
    except accounts.RegisterError, e:
        return flask.render_template('register.html', errors = e.errors)

    title = u"Zarejestrowano"
    message = u"E-mail aktywacyjny został wysłany."
    return flask.render_template('confirm.html',
                                 message = message, title = title)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
