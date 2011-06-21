#!/usr/bin/env python
# -*-coding: utf-8 -*-

# Scalak
# Copyright 2010 Bartosz Szatkowski <bulislaw@linux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import crypt
import random
import functools
import sys
from ConfigParser import SafeConfigParser, Error
import MySQLdb as db
from hashlib import sha1

#XXX
#XXX There is great need to add some status check in all DB operation
#XXX especially for inserts
#XXX

#XXX It would be nice to actually add some level of separation between different
#    area of responsibility by adding submodules
#    utils.user, utils.project, utils.other

class ScalakError(Exception):
    """Main (and for now only one) exception for logic errors in Scalak"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def openDB():
    """Return connection to default Scalak db

    You still need to create cursor and commit/close db
    """

    conf = SafeConfigParser(allow_no_value=True)
    conf.read("/etc/scalak.conf")

    host = conf.get('db', 'host') or 'localhost'
    user = conf.get('db', 'user') or 'scalak'
    passwd = conf.get('db', 'passwd') or 'kalacs'
    dbname = conf.get('db', 'dbname') or 'scalak'

    return db.connect(host = host, user = user, passwd = passwd, db = dbname)

def getCapabilities(user):

    db = openDB()
    c = db.cursor()

    res = c.execute("select action, scope from capabilities where user = %s",
            (user,))

    db.close()

    return c.fetchall()

def listUsers():
    """Return list of ids for all users"""

    db = openDB()
    c = db.cursor()

    res = c.execute("select login from users")
    db.close()

    return [x[0] for x in c.fetchall()]

def userPermission(add, login, scope, action):

    con = openDB()
    c = con.cursor()

    print add, login, scope, action

    if add:
        c.execute('insert into capabilities values (%s, %s, %s)', (login,
                scope, action))
    else:
        c.execute('delete from capabilities where user=%s and action=%s' \
                'and scope=%s', (login, action, scope))

    con.commit()
    c.close()

def findUser(id, project = None):
    """Check if user with given _id_ exists globally or in _project_ if given"""

    db = openDB()
    c = db.cursor()

    if not project:
        res = c.execute("select login from users where login=%s limit 1", (id,))

    else:
        res = c.execute("select login from users, user_project where login=%s \
                and login=user and project=%s limit 1", (id, project))

    db.close()

    if not res:
        return False

    return True

def userProjects(id):
    """Returns all project for user with given _id_"""

    db = openDB()
    c = db.cursor()

    c.execute('select project from user_project where \
            user=%s', (id,))

    db.close()

    return c.fetchall()

def getAdmin(project):
    """Returns admin for given _project_"""

    db = openDB()
    c = db.cursor()

    res = c.execute('select admin from projects where id=%s limit 1', (project,))

    if not res:
        return False

    res = c.fetchone()[0]

    db.close()

    return res

def getOwnedProject(user):
    """Returns all project where _user_ is admin"""

    return [proj for proj in userProjects(user) if user == getAdmin(proj[0])]

def getUserData(id):
    """Get all public user data (without pass hashs)"""

    db = openDB()
    c = db.cursor()

    if not findUser(id):
        raise ScalakError("User doesn't exists")

    c.execute('select login, name, last_name, email, note from users where \
            login=%s limit 1', (id,))

    db.close()

    return c.fetchone()

def getUserRequests(user = None, project = None):
    """Returns 'project join' requests for given data or all requests"""

    db = openDB()
    cur = db.cursor()

    if project and user:
        res = cur.execute('select * from project_requests where user=%s and \
                project=%s limit 1', (user, project))

    elif not project and not user:
        res = cur.execute('select * from project_requests where user=%s \
                limit 1', (id, ))

    elif project and not user:
        res = cur.execute('select * from project_requests where \
                project=%s limit 1', (project, ))

    elif not project and user:
        res = cur.execute('select * from project_requests where user=%s and \
                limit 1', (user, ))

    db.close()

    return cur.fetchall()

def addUserRequest(user, project):
    """Add 'project join' requests"""

    db = openDB()
    c = db.cursor()

    c.execute('insert into project_requests values (%s, %s)',
            (user, project))

    db.close()

def getConfig():
    """Return SafeConfigParser loaded with /etc/scalak.conf"""

    config = SafeConfigParser()
    config.read("/etc/scalak.conf")

    return config

# FIXME it should be more generic 
def getProjectUrl(project):

    return "/p/{0}/trac".format(project)

def htpasswd(password, slt=None):
    """Generating htpasswd hash; salt for checking passwd"""

    if not slt:
        def salt():
            """Returns a string of 2 randome letters"""
            letters = 'abcdefghijklmnopqrstuvwxyz' \
                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                      '0123456789/.'
            return random.choice(letters) + random.choice(letters)

    else:
        def salt():
            return slt

    return crypt.crypt(password, salt())

def valid_password(env, username, password):
    """Check given auth data against DB; env may be None"""

    db = openDB()
    c = db.cursor()

    res = c.execute("select password from users where login=%s limit 1",
            (username,))

    if not res:
        return False

    res = c.fetchone()[0]
    db.close()

    return res == htpasswd(password, res[0] + res[1])

def newUser(login, email, passwd, name = "", lastName="", note = ""):
    """Add user to database

    login, email, passwd are mandatory (passwd in plain text)
    """

    if findUser(login):
        raise ScalakError("User already exists")

    sha1pass = sha1()
    sha1pass.update(passwd)
    sha1pass = sha1pass.hexdigest()

    htpass = htpasswd(passwd)

    con = openDB()
    c = con.cursor()

    c.execute('insert into users values(%s, %s, %s, %s, %s,%s, %s)',
        (login, name, lastName, email, htpass, sha1pass, note))

    con.commit()
    c.close()

def removeUser(login):
    """Removes user from Scalak - user must not be admin of any project"""

    con = openDB()
    c = con.cursor()

    if not findUser(login):
        raise ScalakError("No such user")

    proj = getOwnedProject(login)
    if proj:
        raise ScalakError("Can't remove user {0}, user is admin of " \
                "some projects".format(login, ', '.join([p[0] for p in proj])))

    c.execute('delete from user_project where user=%s', (login,))
    c.execute('delete from users where login=%s', (login,))

    con.commit()
    c.close()

def edit_user(login, field, value):
    """Change user data if parameter is *NOT* None"""

    buf = ""

    if field == 'name':
        buf = 'name="{0}" '.format(value)
    elif field == 'last_name':
        buf  = 'last_name="{0}" '.format(value)
    elif field == 'email':
        buf  = 'email="{0}" '.format(value)
    elif field == 'password':
        sha1pass = sha1()
        sha1pass.update(value)
        sha1pass = sha1pass.hexdigest()
        htpass = htpasswd(value)

        buf = 'password="{0}", '.format(htpass)
        buf += 'sha_password="{0}" '.format(sha1pass)
    elif field == 'note':
        buf += 'note="{0}" '.format(value)
    else:
        raise ScalakError("No such field")

    con = openDB()
    c = con.cursor()

    c.execute('update users set {0} where login="{1}"'.format(buf, login))

    con.commit()
    c.close()
