#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from datetime import date
from subprocess import call
from string import Template
import os
import shutil
import MySQLdb as db
from time import sleep
import sys
from pkg_resources import resource_filename

from scalak.utils import *

__services__ = {}

def registerService(type, subtype, cls):
    """Each services should be registered so Scalak may used it

    Args:
        type - service type name (string) eg. "repository"
        subtype - service type name (string) eg. "svn"
        cls - class corresponding to type and subtype
    """

    if __services__.get((type, subtype)):
        print sys.stderr, "Service {0}:{1} already registered. Skipping." \
                .format(type, subtype)

    __services__[(type, subtype)] = cls


def getClass(type, subtype):
    """Return previously registered object corresponding to type and subtype"""

    return __services__.get((type, subtype))


class Project(object):
    """Main class for all Scalak activity

    Its main responsibility is to build complete Project environment:
        * Directory structure (at config given path)
        * Add project to database
        * Setup Apache connections

    Moreover it have to be "serializable" to database and it should be possible
    to rematerialize it back from database (with all configs, services etc)
    """

    def __init__(self, config=None, id=None, admin=None, create_date=None,
                due_date=None, brief=None, description=None, active = True):
        """Initiates project without actually doing anything

        Parameters:
            db - database connection (MySQLdb object)
            config - ConfigParser.SafeConfigParser
            id - unique string
            admin - user (must already exist in db)
            create_date - datetime.date format
            due_date - after that date project would be highlighted for admin
            breif - short description
            description - long description
            active - disabled project would be read only (in future version)
        """

        self._services = []
        self._id = id
        self._config = config
        self._apacheTemplate = resource_filename('scalak',
                'templates/project.conf')
        self._dir = '/var/scalak/projects/'
        self._path = None

        self.admin = admin
        self.create_date = date.today()
        self.due_date = due_date
        self._brief = brief
        self._description = description
        self.active = active
        self.tags = []

    @property
    def brief(self):
        return self._brief

    @brief.setter
    def brief(self, text):
        if len(text) > 50:
            raise ScalakError("Brief description must be up to 50 characters")
        con = openDB()
        c = con.cursor()
        res = c.execute('update projects set brief=%s where id=%s',
                (text, self.id))
        con.commit()
        c.close()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, text):
        con = openDB()
        c = con.cursor()
        res = c.execute('update projects set description=%s where id=%s',
                (text, self.id))
        con.commit()
        c.close()

    @classmethod
    def projectExists(cls, id):
        """Checks if project with given id exists, raising error when do"""

        con = openDB()
        c = con.cursor()
        res = c.execute('select * from projects where id=%s limit 1',
                (id,))
        c.close()

        if res:
            return True
        return False

    def checkAdmin(self):
        """Checks if user given as admin exists, raising error when not"""

        con = openDB()
        c = con.cursor()
        res = c.execute('select * from users where login=%s limit 1',
                (self.admin,))
        if not res:
            raise ScalakError("User given as admin don't exist in db")

        con.commit()
        c.close()


    def checkData(self):
        """Checks if all necessary atributes are filled up"""
        if not self._id or not len(self._id):
            raise ScalakError("Project id must be supplied")

        if not self._admin or not len(self._admin):
            raise ScalakError("Project admin must be supplied")


    def create(self):
        """Creates project environment (as explained in Project.__doc__)"""

        self.checkAdmin()

        if Project.projectExists(self.id):
            raise ScalakError('Project with given id already exists.')

        if self._config.has_section('general') and \
                self._config.has_option('general', 'projects_dir'):
            self._dir = self._config.get('general', 'projects_dir')
        self._path = os.path.join(self._dir, self.id)

        os.mkdir(self._path)
        os.mkdir(os.path.join(self._path, 'www'))
        with open(os.path.join(self._path, 'www', \
                'index.html'), 'w') as tmp:
            tmp.write('You shall not pass')
        self._initApache()

        con = openDB()
        c = con.cursor()
        c.execute('insert into projects values \
                (%s, %s, %s, %s, %s, %s, %s)',
                (self._id, self.admin, self.create_date, self.due_date,
                self.brief, self.description, self.active))
        c.executemany('insert into tags values (%s, %s)',
                [(self.id, t) for t in self.tags])

        con.commit()
        c.close()

    def addUser(self, id, email=None):
        if not findUser(id):
            raise ScalakError("User with given login doesn't exists.")

        db = openDB()
        c = db.cursor()
        res = c.execute("select user from user_project where user=%s and \
                project=%s limit 1", (id, self.id))
        if res:
            raise ScalakError("User is already project member.")

        c.execute("insert into user_project values (%s, %s)", (id, self.id))

        if not email:
            res = c.execute("select * from users where \
                    login=%s limit 1", (id,))
            if res:
                id, name, last_name, email, passwd, sha_passwd, \
                        note = c.fetchone()

        db.commit()
        c.close()

        for srv in self.getService():
            srv.addUser(id, name, last_name, email, passwd, sha_passwd, note)

    def getRequests(self):
        """User may create request to be accepted as a project member"""

        db = openDB()
        c = db.cursor()
        res = c.execute("select user, email from project_requests, users \
                where project=%s and user = login", (self.id,))
        res = c.fetchall()
        c.close()

        return res

    def setRequest(self, user, accept):
        db = openDB()
        c = db.cursor()
        c.execute("delete from project_requests where project = %s and user = %s",
                (self.id, user))
        db.commit()
        c.close()

        if accept:
            self.addUser(user)

    def removeUser(self, id):
        if id == self.admin:
            raise ScalakError("You can't remove project administrator.")

        db = openDB()
        c = db.cursor()
        c.execute("delete from user_project where user=%s and project=%s",
                (id, self.id))
        db.commit()
        c.close()

        for srv in self.getService():
            srv.removeUser(id)

    def isMemeber(self, id):
        """Checking whether user with given id is project member"""

        db = openDB()
        c = db.cursor()
        c.execute("select login from user_project where user=%s and \
                project=%s limit 1", (id, self.id))
        db.commit()
        c.close()

        if c.fetchone():
            return True
        return False

    def load(self, id, config):
        """Loads project from db, also loads all connected services"""

        con = openDB()
        c = con.cursor()
        res = c.execute('select * from projects where id=%s limit 1',
                (id,))
        if not res:
            raise ScalakError("No such project")
        res = c.fetchone()

        self._id = id
        self.admin = res[1]
        self.create_date = res[2]
        self.due_date = res[3]
        self._brief = res[4]
        self._description = res[5]
        self.active = res[6]
        self._path = os.path.join(self._dir, self.id)

        self._config = config

        # Loading project tags
        res = c.execute('select tag from tags where project=%s',
                (id,))
        if res:
            self.tags = c.fetchall()

        # Loading services
        self._services = []
        res = c.execute('select distinct type, subtype, name  from services \
                where project=%s', (id,))
        tmp = []
        if res:
            tmp = c.fetchall()

        for t, st, n in tmp:
            self.loadService(t, st, n, c)

        con.commit()
        c.close()

    def getUsers(self):
        con = openDB()
        c = con.cursor()
        res = c.execute('select login, name, last_name, email, note \
                from users, user_project where project=%s and user=login',
                (self.id,))
        if not res:
            return []

        return c.fetchall()

    def loadService(self, type, subtype, name, db):
        """Loads given service from data base

        Args:
            type - service type
            subtype - service subtype
            name - service name
            db - mysql database cursor

        All three parameters are necessary because only full path is guaranteed
        to be unique.
        """

        srv = getClass(type, subtype)
        if not srv:
            raise ScalakError("No such service registered: {0},{1}"
                    .format(type, subtype))
        srv = srv()

        res = db.execute('select field, value from services where project=%s and\
                type=%s and subtype=%s and name=%s',
                (self.id, type, subtype, name))
        tmp = []
        if res:
            tmp = db.fetchall()
            srv.load(self, name, tmp)
        self.addService(srv, True)


    def _initApache(self):
        """Copying project specific Apache configuration to .../projects/

        For now its only contains inclusion of services configs, www,
        and general redirection so every non "service" html query would
        end up on www.
        """

        with open(self._apacheTemplate) as confTemplate:
            tmp = ''
            for line in confTemplate.readlines():
                tmp += line

            opt = dict(PROJECT_ID = self.id,
                    PROJECT_PATH = self._path)
            config = Template(tmp).safe_substitute(opt)

        with open(os.path.join(self._dir,
                "{0}.conf".format(self.id)), "w") as confFile:
            confFile.write(config)

    def getService(self, type = None, subtype = None, name = None):
        """Return service with given type, subtype and name (all strings).

        If any field is None then this field is ignored, but You can ignore
        only fields on the right of the one already supplied.
        so. type = "repository", subtype = None, name = None -> OK
            type = None, subtype = None, name = "foospam" -> WRONG
        """

        res = []
        for srv in self._services:
            if (type is None or srv.type == type) and \
                    (subtype is None or srv.subtype == subtype) and \
                    (name is None or srv.name == name):
                        res.append(srv)
        return res

    def addService(self, srv, load=False):
        """Adds new service to project

        srv - service to add subclass of Service
        load - load must be true if You are loading service from db,
                    false when adding new service

        Each service path (type:subtype:name) must be unique, services may add
        some further restrictions.
        """
        if len(self.getService(srv.type, srv.subtype, srv.name)) and not \
                srv.name is None:
            raise ScalakError("Service {0}:{1} with given name ({2})" \
                    " already exists.".format(srv.type, srv.subtype,
                    srv.name))

        if not load:
            srv.deploy(self, self._config)
            srv.save()
        self._services.append(srv)

    def delService(self, srv):
        """Deletes given service (some service may not be deleted)

        srv - service to delete subclass of Service

        Its only delete like in "i don't want this repository any more", so
        You can't delete eg. Trac.
        """

        srv.remove()
        try:
            self._services.remove(srv)
        except ValueError:
            pass
        con = openDB()
        c = con.cursor()
        c.execute("delete from services where project=%s and type=%s \
                and subtype=%s and name=%s", (self.id, srv.type,
                    srv.subtype, srv.name))
        con.commit()
        c.close()

    @property
    def id(self):
        """Return project id

        Id must be unique and its not changeable in current Scalak version.
        """
        return self._id

    def remove(self, quiet=False):
        """Removes project with all settings and services

            quiet = True won't wait for 5 sec before procede
        """

        if not quiet:
            print "Going to delete project: {0}. You can cancel (by ctrl-c):" \
                .format(self.id),
            sys.stdout.flush()

            for x in reversed(range(1, 6)):
                print x,
                sys.stdout.flush()
                sleep(1)

            print ""

        for srv in self._services:
            srv.remove()

        shutil.rmtree(self._path)
        os.remove(os.path.join(self._dir, "{0}.conf".format(self.id)))

        con = openDB()
        c = con.cursor()
        c.execute("delete from services where project=%s", (self.id,))
        c.execute("delete from tags where project=%s", (self.id,))
        c.execute("delete from user_project where project=%s", (self.id,))
        c.execute("delete from projects where id=%s", (self.id,))
        con.commit()
        c.close()
