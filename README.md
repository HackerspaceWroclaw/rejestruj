Rejestruj -- registration application for Hackerspace Wrocław
=============================================================

This application is developed for Hackerspace Wrocław to manage LDAP accounts,
which give access to our wiki, git and several other services.


Installation
------------

Simple WSGI application, requiring [Flask](http://flask.pocoo.org/).
Python 2.6 or newer.

**TODO**: be more verbose.

### Requirements

  * Python 2.6+
  * Flask 0.6+ (older versions were not checked)
  * [python-ldap](http://www.python-ldap.org/) (2.4 was used)
  * XML-RPC server for Mailman lists (e.g.
    [xmlrpcd](http://dozzie.jarowit.net/trac/wiki/xmlrpcd))
  * LDAP server to manage


License
-------

This software is released under the GPL version 3. See LICENSE for details.
