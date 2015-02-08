#!/usr/bin/python

import flask
import rejestruj.settings

#-----------------------------------------------------------------------------

app = flask.Flask(__name__)
app.config.from_object(rejestruj.settings)

#-----------------------------------------------------------------------------

@app.route("/")
def index():
    return flask.render_template('index.html')

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
