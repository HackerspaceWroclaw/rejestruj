#!/usr/bin/python

import db
import flask
import time
import sha

#-----------------------------------------------------------------------------

class Session:
    def __init__(self, config, dbconn = None):
        if dbconn is not None:
            self.dbconn = dbconn
        else:
            self.dbconn = db.connection(config)
        self.session_var = config['SESSION_VARIABLE']
        self.session_id = flask.request.cookies.get(self.session_var)
        if self.session_id is None:
            # data to calculate session ID
            data = "%s -> %s @%.6f <%s>" % (
                flask.request.remote_addr,
                flask.request.host_url,
                time.time(),
                config['SECRET_KEY'],
            )
            self.session_id = sha.sha(data).hexdigest()
        self._content = db.load_session(self.dbconn, self.session_id)

    def cookie(self):
        return (self.session_var, self.session_id)

    def save(self):
        db.save_session(self.dbconn, self.session_id, self._content)

    def delete(self):
        db.delete_session(self.dbconn, self.session_id)

    def __setitem__(self, key, value):
        self._content[key] = value

    def __delitem__(self, key):
        if key in self._content:
            del self._content[key]

    def __getitem__(self, key):
        return self._content.get(key)

    def __contains__(self, key):
        return key in self._content

    def __len__(self):
        return len(self._content)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
