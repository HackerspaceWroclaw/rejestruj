#!/usr/bin/python

import sqlite3
import accounts
import json
import time

#-----------------------------------------------------------------------------

def connection(config):
    dbconn = sqlite3.connect(
        config['DATABASE_FILE_ABS'],
        isolation_level = "IMMEDIATE",
    )
    create_tables(dbconn)
    return dbconn

#-----------------------------------------------------------------------------

def save_form(dbconn, token, nick, email, firstname, lastname, password):
    crypt_password = accounts.passwd(password)
    cursor = dbconn.cursor().execute(
        """
        INSERT INTO pending
            (token, nick, email, firstname, lastname, crypt_password)
            VALUES
            (?, ?, ?, ?, ?, ?)
        """,
        (token, nick, email, firstname, lastname, crypt_password)
    )
    cursor.close()
    dbconn.commit()

def load_form(dbconn, token):
    cursor = dbconn.cursor()
    cursor.execute(
        """
        SELECT nick, email, firstname, lastname, crypt_password
            FROM pending
            WHERE token = ?
        """,
        (token,)
    )
    result = cursor.fetchone()
    if result is None:
        cursor.close()
        return None

    (nick, email, firstname, lastname, crypt_password) = result
    # XXX: deleting all attempts for `nick' registration
    cursor.execute("DELETE FROM pending WHERE nick = ?", (nick,))
    cursor.close()
    dbconn.commit()
    return (nick, email, firstname, lastname, crypt_password)

#-----------------------------------------------------------------------------

def save_session(dbconn, session_id, variables):
    access_time = time.time()
    session_data = json.dumps(variables, sort_keys = True)

    cursor = dbconn.cursor()
    cursor.execute("INSERT OR IGNORE INTO session VALUES (?, ?, ?)",
              (session_id, session_data, access_time))
    if cursor.rowcount == 0:
        cursor.execute(
            """
            UPDATE session
                SET variables = ?, last_access = ?
                WHERE session_id = ?
            """,
            (session_data, access_time, session_id)
        )
    cursor.close()
    dbconn.commit()

def delete_session(dbconn, session_id):
    cursor = dbconn.cursor()
    cursor.execute("DELETE FROM session WHERE session_id = ?", (session_id,))
    cursor.close()
    dbconn.commit()

def load_session(dbconn, session_id):
    cursor = dbconn.cursor()
    cursor.execute("SELECT variables FROM session WHERE session_id = ?",
                   (session_id,))
    result = cursor.fetchone()
    cursor.close()
    if result is None:
        return {}
    else:
        return json.loads(result[0])

#-----------------------------------------------------------------------------

def has_table(dbconn, name):
    cursor = dbconn.cursor()
    cursor.execute(
        '''
        SELECT count(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
        ''',
        (name,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] > 0

def create_tables(dbconn):
    if not has_table(dbconn, "pending"):
        dbconn.cursor().execute("""
            CREATE TABLE pending (
                token TEXT PRIMARY KEY,
                nick  TEXT,
                email TEXT,
                firstname TEXT,
                lastname  TEXT,
                crypt_password TEXT
            )
        """)

    if not has_table(dbconn, "session"):
        dbconn.cursor().execute("""
            CREATE TABLE session (
                session_id TEXT PRIMARY KEY,
                variables TEXT,
                last_access INTEGER
            )
        """)

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
