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

#XXX
#XXX There is great need to add some status check in all DB operation
#XXX especially for inserts
#XXX

#XXX It would be nice to actually add some level of separation between different
#    area of responsibility by adding submodules
#    utils.user, utils.project, utils.other

class ScalakError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def openDB():

    conf = SafeConfigParser(allow_no_value=True)
    conf.read("/etc/scalak.conf")
    host = conf.get('db', 'host') or 'localhost'
    user = conf.get('db', 'user') or 'scalak'
    passwd = conf.get('db', 'passwd') or 'kalacs'
    dbname = conf.get('db', 'dbname') or 'scalak'

    return db.connect(host = host, user = user, passwd = passwd, db = dbname)

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

    c.execute('select login, name, last_name, email, note from users where \
            login=%s limit 1', (id,))

    db.close()

    return c.fetchone()

def getUserRequests(user = None, project = None):
    """Returns 'project join' requests for given data or all requsts"""

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

def valid_password(environ, username, password):
    db = openDB()
    c = db.cursor()

    res = c.execute("select password from users where login=%s limit 1", (username,))

    if not res:
        return False

    res = c.fetchone()[0]
    db.close()

    return res == htpasswd(password, res[0] + res[1])
