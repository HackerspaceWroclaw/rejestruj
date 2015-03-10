#!/usr/bin/python

import sqlite3
import accounts
import json
import time

#-----------------------------------------------------------------------------

class DB:
    def __init__(self, config):
        self.conn = sqlite3.connect(
            config['DATABASE_FILE_ABS'],
            isolation_level = "IMMEDIATE",
        )
        self.create_tables()

    #-------------------------------------------------------
    # creating missing tables {{{

    def has_table(self, name):
        with self.conn as cursor:
            result = cursor.execute(
                '''
                SELECT count(*)
                    FROM sqlite_master
                    WHERE type = 'table' AND name = ?
                ''',
                (name,)
            ).fetchone()
            return result[0] > 0

    def create_tables(self):
        with self.conn as cursor:
            if not self.has_table("pending"):
                cursor.execute("""
                    CREATE TABLE pending (
                        token TEXT PRIMARY KEY,
                        nick  TEXT,
                        email TEXT,
                        firstname TEXT,
                        lastname  TEXT,
                        crypt_password TEXT
                    )
                """)

            if not self.has_table("password_reset"):
                cursor.execute("""
                    CREATE TABLE password_reset (
                        nick TEXT PRIMARY KEY,
                        token TEXT
                    )
                """)

            if not self.has_table("session"):
                cursor.execute("""
                    CREATE TABLE session (
                        session_id TEXT PRIMARY KEY,
                        variables TEXT,
                        last_access INTEGER
                    )
                """)

    # }}}
    #-------------------------------------------------------
    # register forms {{{

    def save_form(self, token, nick, email, firstname, lastname, password):
        with self.conn as cursor:
            cursor.execute(
                """
                INSERT INTO pending
                    (token, nick, email, firstname, lastname, crypt_password)
                    VALUES
                    (?, ?, ?, ?, ?, ?)
                """,
                (token, nick, email, firstname, lastname, password)
            )

    def load_form(self, token):
        with self.conn as cursor:
            result = cursor.execute(
                """
                SELECT nick, email, firstname, lastname, crypt_password
                    FROM pending
                    WHERE token = ?
                """,
                (token,)
            ).fetchone()
            # None | (nick, email, firstname, lastname, crypt_password)
            return result

    def delete_all_forms_for(self, nick):
        # XXX: deleting all attempts for `nick' registration
        with self.conn as cursor:
            cursor.execute("DELETE FROM pending WHERE nick = ?", (nick,))

    # }}}
    #-------------------------------------------------------
    # password reset confirmations {{{

    def save_reset_password_token(self, token, nick):
        with self.conn as cursor:
            cursor.execute(
                """
                DELETE FROM password_reset WHERE nick = ?
                """,
                (nick,)
            )
            cursor.execute(
                """
                INSERT INTO password_reset (nick, token) VALUES (?, ?)
                """,
                (nick, token)
            )

    def load_reset_password_token(self, token):
        with self.conn as cursor:
            result = cursor.execute(
                """
                SELECT nick
                    FROM password_reset
                    WHERE token = ?
                """,
                (token,)
            ).fetchone()
            if result is None:
                return None
            return result[0] # return just nick

    def delete_reset_password_token(self, token):
        with self.conn as cursor:
            cursor.execute(
                """
                DELETE FROM password_reset WHERE token = ?
                """,
                (token,)
            )

    # }}}
    #-------------------------------------------------------
    # HTTP sessions {{{

    def save_session(self, session_id, variables):
        access_time = time.time()
        session_data = json.dumps(variables, sort_keys = True)

        with self.conn as cursor:
            result = cursor.execute(
                """
                INSERT OR IGNORE INTO session VALUES (?, ?, ?)
                """,
                (session_id, session_data, access_time)
            )
            if result.rowcount == 0:
                cursor.execute(
                    """
                    UPDATE session
                        SET variables = ?, last_access = ?
                        WHERE session_id = ?
                    """,
                    (session_data, access_time, session_id)
                )

    def delete_session(self, session_id):
        with self.conn as cursor:
            cursor.execute("DELETE FROM session WHERE session_id = ?",
                           (session_id,))

    def load_session(self, session_id):
        with self.conn as cursor:
            result = cursor.execute(
                """
                SELECT variables FROM session WHERE session_id = ?
                """,
                (session_id,)
            ).fetchone()
            if result is None:
                return {}
            else:
                return json.loads(result[0])

    # }}}
    #-------------------------------------------------------

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
