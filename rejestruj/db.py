#!/usr/bin/python

import sqlite3
import accounts

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

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
