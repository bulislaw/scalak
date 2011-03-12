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

class ScalakError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def openDB():
    host = 'localhost'
    user = 'scalak'
    passwd = 'scalak'
    dbname = 'scalak'
    return db.connect(host = host, user = user, passwd = passwd, db = dbname)

def htpasswd(password, slt=None):
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

def findUser(id, project = None):
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

def getAdmin(project):
    db = openDB()
    c = db.cursor()

    res = c.execute("select admin from projects where id=%s limit 1", (project,))

    if not res:
        return False

    res = c.fetchone()[0]

    db.close()

    return res

def getConfig():
    config = SafeConfigParser()
    config.read("/etc/scalak.conf")
    return config

def getProjectUrl(project):
    return "/p/{0}/trac".format(project)

def valid_password(environ, username, password):
    db = openDB()
    c = db.cursor()

    res = c.execute("select password from users where login=%s limit 1", (username,))

    if not res:
        return False

    res = c.fetchone()[0]
    db.close()

    return res == htpasswd(password, res[0] + res[1])

