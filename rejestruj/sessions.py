#!/usr/bin/python

import fdb
import flask
import time
import sha

#-----------------------------------------------------------------------------

class Session:
    def __init__(self, config):
        self.db = fdb.DB(config)
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
            self._content = {}
            self._messages = []
        else:
            data = self.db.load_session(self.session_id)
            self._content = data.get('variables', {})
            self._messages = data.get('messages', [])

    def has_messages(self):
        return (len(self._messages) > 0)

    def pop_message(self):
        return self._messages.pop(0)

    def add_message(self, message):
        self._messages.append(message)

    def cookie(self):
        return (self.session_var, self.session_id)

    def save(self):
        data = {
            'messages': self._messages,
            'variables': self._content,
        }
        self.db.save_session(self.session_id, data)

    def delete(self):
        self.db.delete_session(self.session_id)

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
