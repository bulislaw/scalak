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
import stat
from time import sleep
import sys

from pkg_resources import resource_string

from trac.env import Environment as Env
from trac.db.api import with_transaction
from trac.perm import PermissionSystem

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
        self._apacheTemplate = os.path.join(os.path.dirname(__file__), 'templates/project.conf')
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


class Service(object):
    """Base class for all other project's services

    Services are divided by type (like 'trac', 'repository') and subtype
    (like 'svn', 'git'), furthermore each service may have name.

    All these adds to be service path: type:subtype:name, which must be unique
    under each project, but concrete service may add some further restriction
    eg. only one service with given type.
    """

    _type = None
    _subtype = None
    _project = None
    _name = None
    _config = None
    _dir = "/var/scalak/projects/"
    _eggCache = "/var/scalak/python_egg_cache"


    def deploy(self, project, config):
        """Creates and configures service

        Parameters:
            project - Project instance (service would be added to it)
            config - ConfigParser.SafeconfigParser

        Deploy should do all service side steps, after adding service to
        project, needed to build working service.

        Its only base function, subclasses should overload it and call for
        this one in subclass.deploy
        """

        self._config = config
        self._project = project
        if self._config.has_section('general'):
            if config.has_option('general', 'projects_dir'):
                self._dir = config.get('general', 'projects_dir')

            if config.has_option('general', 'python_egg_cache'):
                self._eggCache = config.get('general', 'python_egg_cache')


    def save(self):
        """Saves service to db, subclass decides which args needs saving"""
        values = self._serialize()
        con = openDB()
        c = con.cursor()
        c.executemany("insert into services values \
                (%s, %s, %s, %s, %s, %s)",
                [(self._project.id, self.type, self.subtype, self.name,
                    tup[0], tup[1]) for tup in values])
        con.commit()
        c.close()


    def _serialize(self):
        """Each subclass should return its own argument

        Return:
            list of tuples (key, value)

        Returned tuples will be saved to db and then service would be
        created and suplied with that values
        """
        return [('none', 'none')]


    def remove(self):
        pass


    def _updateConfig(self):
        pass


    def _runCommand(self, args, command=None, quiet=False):
        if command is None:
            command = self._command

        if not command:
            return -1
        args = [command] + args
        stdout = None
        if quiet:
            stdout = open('/dev/null', 'ra')

        ret = call(args, stdout = stdout)
        if stdout:
            stdout.close()
        return ret;


    def addUser(self, login, name = None, last_name = None, email = None,
            passwd = None, sha_passwd = None, note = None):
        pass

    def removeUser(self, id):
        pass

    @property
    def type(self):
        return self._type

    @property
    def subtype(self):
        return self._subtype

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    @config.setter
    def config(self, conf):
        self._config = conf
        self._updateConfig()


class Trac(Service):
    """Service integrating Scalak with Trac"""


    _type = "trac"
    _subtype = "trac"

    _dbSpec = "sqlite:db/trac.db"
    _command = "trac-admin"
    _tracConfig = os.path.join(os.path.dirname(__file__), "templates/trac/trac.ini.template")
    _apacheConfig = os.path.join(os.path.dirname(__file__), "templates/trac/trac.conf")

    # For config file templates 
    _options = dict(PLUGINS_DIR='',
                    PROJECT_ADMIN='',
                    PROJECT_DESCRIPTION='',
                    PROJECT_ID='',
                    PROJECT_DIR='',
                    TRAC_PATH='')

    _pluginsDir = "/var/scalak/trac_plugins"
    _tracAdminDir = "/usr/local/bin/trac-admin"
    _tracPath = None


    def __init__(self, name = "main"):
        self._name = name


    def _serialize(self):
        """Returns valuese needed to be serialized to data base

        Return:
            list of tuples (key, value)

        """

        return [('_pluginsDir', self._pluginsDir), 
                ('_tracAdminDir', self._tracAdminDir),
                ('_dir', self._dir),
                ('_eggCache', self._eggCache)]


    def deploy(self, project, config):
        """Creates and connect Trac instance with Scalak and Apache

        Only one instance per project!

        Parameters:
            project - Project instance (service would be added to it)
            config - ConfigParser.SafeconfigParser

        Steps:
            * Initenv Trac in .../projects/<name>/trac/
            * Configure and copy trac.ini
            * Copy and fill Apache config file
        """

        super(Trac, self).deploy(project, config)

        if config.has_section('trac'):
            if config.has_option('trac', 'plugins_dir'):
                self._pluginsDir = config.get('trac', 'plugins_dir')
            if config.has_option('trac', 'trac_admin_dir'):
                self._tracAdminDir = config.get('trac', 'trac_admin_dir')

        self._checkSingleton()

        self._tracPath = os.path.join(self._dir, self._project.id, "trac/")
        os.mkdir(self._tracPath)

        if self._runCommand([self._tracPath,
                "initenv", project.id, self._dbSpec]):
            raise ScalakError("Error when trying to init new " 
                    "Trac instance.")

        self._options['PROJECT_ADMIN'] = self._project.admin
        self._options['PROJECT_DESCRIPTION'] = self._project.description
        self._options['PROJECT_ID'] = self._project.id
        self._options['TRAC_PATH'] = self._dir + self._project.id + "/trac/"
        self._options['PLUGINS_DIR'] = self._pluginsDir
        self._options['PROJECT_DIR'] = self._dir

        self._configure(self._tracPath)
        self._configureApache(self._project._path)

        # Adding admin for Trac
        if self._runCommand([self._tracPath,
                "permission add", project.admin, 'TRAC_ADMIN']):
            raise ScalakError("Error when trying to init new "
                    "Trac instance.")

        # Upgrading project - some plugins needs it
        if self._runCommand([self._tracPath, "upgrade"]):
            raise ScalakError("Error when trying to upgrade "
                    "Trac instance.")

        # Create authz file for future repo (empty for now)
        os.mkdir(os.path.join(self._dir, self._project.id, 'repos/'))
        with open(os.path.join(self._dir, self._project.id, 'repos/authz'), 'w')\
                as authz:
            authz.write("[/]\n* = rw\n")


    def load(self, project, name, values):
        """Loads Trac service object from values

        Arg:
            values - list of tuples ('name', value)
        """

        self._name = name
        self._project = project
        for v in values:
            setattr(self, v[0], v[1])

        self._tracPath = os.path.join(self._dir, self._project.id, "trac/")

        self._options['PROJECT_ADMIN'] = self._project.admin
        self._options['PROJECT_DESCRIPTION'] = self._project.description
        self._options['PROJECT_ID'] = self._project.id
        self._options['TRAC_PATH'] = self._dir + self._project.id + "/trac/"
        self._options['PLUGINS_DIR'] = self._pluginsDir


    def _configure(self, tracDir):
        """Takes template for trac.ini and save it, filled up, into project dir

            tracDir - path to trac instance
        """

        with open(self._tracConfig) as confTemplate:
            tmp = ''
            for line in confTemplate.readlines():
                tmp += line

            config = Template(tmp).safe_substitute(self._options)

        with open(os.path.join(tracDir, "conf/trac.ini"), "w") as confFile:
            confFile.write(config)


    def _checkSingleton(self):
        """Checks if there is already Trac instance in project

        There is only one Trac instance per project allowed
        """
        if len(self._project.getService(self.type)):
            raise ScalakError("Trac service already exists, only one Trac" \
                    " nstance per project allowed.")


    def _configureApache(self, projectDir):
        """Takes template for Apache config and save it filled up

            Templates would add Trac instance to Apache so it could be
            accesed from net.

            projectDir - path to project
        """

        with open(self._apacheConfig) as confTemplate:
            tmp = ''
            for line in confTemplate.readlines():
                tmp += line

            config = Template(tmp).safe_substitute(self._options)

        with open(os.path.join(projectDir, "trac.conf"), "w") as confFile:
            confFile.write(config)


    def addRepository(self, name, path, type):
        """Connects repository to trac

        Parameters:
            name - repository naem
            path - path to the repository
            type - trac repository type 'svn', 'hg'
        """

        if self._runCommand([self._tracPath,
                "repository add", name, path, type ]):
            raise ScalakError("Error when trying to add new repository.")

        if self._runCommand([self._tracPath,
                "repository resync", name]):
            raise ScalakError("Error when trying to resync new repository.")

        # install hooks
        postCommit = os.path.exists(os.path.join(path, 'hooks', 'post-commit'))
        revprop = os.path.exists(os.path.join(path, 'hooks', 'post-revprop-change'))

        if type == "svn":
            with open(os.path.join(path, 'hooks', 'post-commit'), 'a') as file:
                if not postCommit:
                    file.write('#!/bin/bash\n')
                file.write('export PYTHON_EGG_CACHE={0}\n{1} {2} changeset added "$1" "$2"\n'
                        .format(self._eggCache, self._tracAdminDir, self._tracPath))

            os.chmod(os.path.join(path, 'hooks', 'post-commit'),
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                    stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | 
                    stat.S_IXOTH)

            with open(os.path.join(path, 'hooks', 'post-revprop-change'), 'a') as file:
                if not revprop:
                    file.write('#!/bin/bash\n')
                file.write('export PYTHON_EGG_CACHE={0}\n{1} {2} changset modified "$1" "$2"\n'
                        .format(self._eggCache, self._tracAdminDir, self._tracPath))

            os.chmod(os.path.join(path, 'hooks', 'post-revprop-change'),
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                    stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | 
                    stat.S_IXOTH)

    def delRepository(self, name):
        """Disconnects repository from trac

        Parameters:
            name - repository naem
            path - path to the repository
            type - trac repository type 'svn', 'hg'
        """

        if self._runCommand([self._tracPath,
                "repository remove", name]):
            raise ScalakError("Error when trying to add new repository.")


    def addUser(self, login, name = None, last_name = None, email = None, 
            passwd = None, sha_passwd = None, note = None):

        env = Env(self._tracPath)
        @with_transaction(env)
        def add_user(db):
            c = db.cursor()
            c.execute("delete from session_attribute where sid=%s", (login,))
            c.execute("delete from permission where username=%s", (login,))
            c.execute("insert into session_attribute (sid, authenticated, \
                    name, value) values (%s, 1, 'email', %s)", (login, email))
            c.execute("insert into session_attribute (sid, authenticated, \
                    name, value) values (%s, 1, 'name', %s)", (login, 
                    "{0} {1}".format(name, last_name)))
            c.execute("insert into permission values (%s, \"BROWSER_VIEW\")", \
                    (login,))
            db.commit()
            c.close()

    def removeUser(self, id):
        env = Env(self._tracPath)
        @with_transaction(env)
        def remove_user(db):
            c = db.cursor()
            c.execute("delete from session_attribute where sid=%s", (id,))
            c.execute("delete from permission where username=%s", (id,))

registerService(Trac._type, Trac._subtype, Trac)


class Repository(Service):
    """Base class for all repositories"""

    _type = 'repository'
    _stdname = None

    def deploy(self, project, config):
        """Creates and connects repository to project"""

        super(Repository, self).deploy(project, config)
        repos = project.getService(self._type, self._subtype)
        self._stdname = self._subtype + str(len(repos))
        i = len(repos)
        while project.getService(self._type, self._subtype, self._stdname):
            i += 1
            self._stdname = self._subtype + str(i)


    def _connectTrac(self):
        """Connects repository to Trac"""

        trac = self._project.getService(Trac._type)
        if len(trac):
            trac[0].addRepository(self._name, self._repoPath, self._subtype)
        else:
            raise ScalakError("There is no Trac instance for given project."
                    " Contact Scalak administrator.")

    def _disconnectTrac(self):
        """Connects repository to Trac"""

        trac = self._project.getService(Trac._type)
        if len(trac):
            trac[0].delRepository(self._name)
        else:
            raise ScalakError("There is no Trac instance for given project."
                    " Contact Scalak administrator.")

    def remove(self):
        self._disconnectTrac()
        shutil.rmtree(self._repoPath)


class Subversion(Repository):
    """Subversion repository service"""

    _subtype = "svn"
    _command = "svn"

    _adminCommand = "svnadmin"
    _apacheConfig = os.path.join(os.path.dirname(__file__), 'templates/svn/svn.conf')
    _repoConfig = os.path.join(os.path.dirname(__file__),  "templates/svn/repo.conf")

    _svnPath = None
    _repoPath = None

    def __init__(self, name = None):
        self._name = name



    def deploy(self, project, config):
        """Creates subversion repository and connect it to project

        Parameters:
            project - Project instance (service would be added to it)
            config - ConfigParser.SafeconfigParser
        Steps:
            * create repository
            * add apache support
            * add trac connection
            * add acl support
        """

        super(Subversion, self).deploy(project, config)
        if self._name is None:
            self._name = self._stdname
        self._svnPath = self._dir + self._project.id + "/repos/svn/" 
        self._repoPath = self._svnPath + self._name
        try:
            os.makedirs(self._repoPath)
        except os.error:
            pass

        if self._runCommand(['create', self._repoPath], 
                self._adminCommand):
            raise ScalakError("Error while trying to create " \
                    "svn repository.")

        self._configure()
        self._connectTrac()


    def _serialize(self):
        """Returns valuese needed to be serialized to data base

        Return:
            list of tuples (key, value)

        """

        return [('_dir', self._dir)]


    def load(self, project, name, values):
        """Loads Trac service object from values

        Arg:
            values - list of tuples ('name', value)
        """

        self._name = name
        self._project = project

        for v in values:
            setattr(self, v[0], v[1])

        self._svnPath = self._dir + self._project.id + "/repos/svn/" 
        self._repoPath = self._svnPath + self._name



    def _configure(self):
        options = dict(REPO_PATH=self._repoPath,
                        PROJECT_ID=self._project.id,
                        PROJECT_PATH= self._svnPath,
                        PROJECT_DIR= self._dir,
                        REPO_NAME=self._name)

        with open(self._apacheConfig) as confTemplate:
            tmp = ''
            for line in confTemplate.readlines():
                tmp += line

            config = Template(tmp).safe_substitute(options)

        with open(os.path.join(self._dir, self._project.id, 
                "svn.conf"), "w") as confFile:
            confFile.write(config)


        with open(self._repoConfig) as confTemplate:
            tmp = ''
            for line in confTemplate.readlines():
                tmp += line

            config = Template(tmp).safe_substitute(options)

        with open(os.path.join(self._svnPath, 
                "{0}.conf".format(self._name)), "w") as confFile:
            confFile.write(config)

    def remove(self):
        super(Subversion, self).remove()

        # Deleting connected authz lines
        with open(os.path.join(self._dir, self._project.id, "repos/authz"), \
                'r') as file:
            buf = file.readlines()

        match = False
        res = []
        for line in buf:
            if line.startswith("[{0}:".format(self.name)):
                match = True
                continue

            if line.startswith("["):
                match = False

            if not match:
                res.append(line)

        with open(os.path.join(self._dir, self._project.id, "repos/authz"), \
                'w') as file:
            file.writelines(res)

registerService(Subversion._type, Subversion._subtype, Subversion)


class Mercurial(Repository):
    _subtype = "hg"

    _command = "hg"

    _apacheConfig =  os.path.join(os.path.dirname(__file__), 'templates/hg/hg.conf')
    _hgConfig =  os.path.join(os.path.dirname(__file__), "templates/hg/hgweb.config")
    _hgCgi =  os.path.join(os.path.dirname(__file__), 'templates/hg/hgwebdir.cgi')

    _hgPath = None
    _repoPath = None

    def __init__(self, name = None):
        self._name = name



    def deploy(self, project, config):
        super(Mercurial, self).deploy(project, config)

        if self._name is None:
            self._name = self._stdname

        self._hgPath = self._dir + project.id + "/repos/hg/"
        self._repoPath = self._hgPath + self._name
        try:
            os.makedirs(self._repoPath)
        except os.error:
            pass

        if self._runCommand(['init', self._repoPath, '-v']):
            raise ScalakError("Error while trying to create hg repository.")

        self._configure()
        self._connectTrac()


    def _serialize(self):
        """Returns valuese needed to be serialized to data base

        Return:
            list of tuples (key, value)

        """

        return [('_dir', self._dir)]


    def load(self, project, name, values):
        """Loads Trac service object from values

        Arg:
            values - list of tuples ('name', value)
        """

        self._name = name
        self._project = project
        for v in values:
            setattr(self, v[0], v[1])

        self._hgPath = self._dir + project.id + "/repos/hg/"
        self._repoPath = self._hgPath + self._name


    def _configure(self):
        options = dict(REPO_PATH=self._hgPath,
                        PROJECT_ID=self._project.id,
                        PROJECT_PATH= self._repoPath,
                        REPO_NAME=self._name)

        if not os.path.exists(os.path.join(self._project._path, "hg.conf")):
            with open(self._apacheConfig) as confTemplate:
                tmp = ''
                for line in confTemplate.readlines():
                    tmp += line

                config = Template(tmp).safe_substitute(options)

            with open(os.path.join(self._dir, self._project.id, 
                    "hg.conf"), "w") as confFile:
                confFile.write(config)


        if not os.path.exists(os.path.join(self._hgPath, "hgweb.config")):
            with open(self._hgConfig) as confTemplate:
                tmp = ''
                for line in confTemplate.readlines():
                    tmp += line

                config = Template(tmp).safe_substitute(options)

            with open(os.path.join(self._hgPath, 
                    "hgweb.config"), "w") as confFile:
                confFile.write(config)

        if not os.path.exists(os.path.join(self._hgPath, 'hgwebdir.cgi')):
            shutil.copy2(os.path.join(os.path.dirname(__file__), 'templates/hg/hgwebdir.cgi'), 
                    os.path.join(self._hgPath, 'hgwebdir.cgi'))
            os.chmod(os.path.join(self._hgPath, 'hgwebdir.cgi'), 
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                    stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | 
                    stat.S_IXOTH)

        shutil.copy2(os.path.join(os.path.dirname(__file__), 'templates/hg/hgrc'), 
                os.path.join(self._repoPath, '.hg'))

registerService(Mercurial._type, Mercurial._subtype, Mercurial)

class Mailman(Service):
    """Mailing list suport for Scalak

    Mailman module is hard one - Mailman don't have extensive cli scripts,
    so i have to use some internal mechanisms 
    """

    _type = "mailing"
    _subtype = "mailman"

    _command = None

    _mailman_dir = '/usr/lib/mailman/'
    _aliases_config = None
    _aliases_file = '/etc/aliases'
    _aliases_update = 'newaliases'

    _aliasesTpl = Template("""
$LIST_NAME:              "|/var/lib/mailman/mail/mailman post mailman"
$LIST_NAME-admin:        "|/var/lib/mailman/mail/mailman admin mailman"
$LIST_NAME-bounces:      "|/var/lib/mailman/mail/mailman bounces mailman"
$LIST_NAME-confirm:      "|/var/lib/mailman/mail/mailman confirm mailman"
$LIST_NAME-join:         "|/var/lib/mailman/mail/mailman join mailman"
$LIST_NAME-leave:        "|/var/lib/mailman/mail/mailman leave mailman"
$LIST_NAME-owner:        "|/var/lib/mailman/mail/mailman owner mailman"
$LIST_NAME-request:      "|/var/lib/mailman/mail/mailman request mailman"
$LIST_NAME-subscribe:    "|/var/lib/mailman/mail/mailman subscribe mailman"
$LIST_NAME-unsubscribe:  "|/var/lib/mailman/mail/mailman unsubscribe mailman" 
""")


    def __init__(self, name = None):
        """Name is only part of real list name - full name is <project-name>-<name>-<list-spec>"""

        self._name = "devel"
        if name:
            self._name = name



    def _initPath(self):
        Utils.list_exists("test")


    def _serialize(self):
        """Returns valuese needed to be serialized to data base

        Return:
            list of tuples (key, value)
        """

        return [('_mailman_dir', self._mailman_dir), 
                ('_aliases_file', self._aliases_file),
                ('_aliases_update', self._aliases_update),
                ('_aliases_config', self._aliases_config)]


    def load(self, project, name, values):
        """Loads Trac service object from values

        Arg:
            values - list of tuples ('name', value)
        """

        self._name = name
        self._project = project
        for v in values:
            setattr(self, v[0], v[1])
        self.listname = '{0}-{1}'.format(self._project.id, self._name)
        self._bin_dir = os.path.join(self._mailman_dir, 'bin/')


    def deploy(self, project, config):
        """Creates and connect mailman instance with Scalak

        This part is kind of tricky becouse mailman provide minimal cli 
        interface, that is definitly not sufficient.


        Parameters:
            project - Project instance (service would be added to it)
            config - ConfigParser.SafeconfigParser

        Complications:
            Mailman is using SHA-digested passwords, Scalak (mostly becouse
                of Apache) htpasswd. Most basic (and curently used) method
                to supply the SHA password is to keep it in db (they are
                generated with htpasswd)

        Steps:
            * Reading configuration for mailman bin directory, aliases, alias
                update command
            * Reading sha admin password (scalak keeps passwords in htpasswd
                mainly becouse of apache, so i add additional field with sha
                passwd)
            * Then is kind of balck box - mailman internal callbacks, used
                code from Mailman:bin/newlist
            * Configuration part - adding and updating aliases
        """

        super(Mailman, self).deploy(project, config)

        if self._config.has_section('mailman'):
            # Path to mailman install directory
            if config.has_option('mailman', 'mailman_dir'):
                self._mailman_dir = config.get('mailman', 'mailman_dir')


            # Path to mta aliases file
            if config.has_option('mailman', 'aliases_file'):
                self._aliases_file = config.get('mailman', 'aliases_file')

            # Command tu update aliases list
            if config.has_option('mailman', 'aliases_update'):
                self._aliases_update = config.get('mailman', 'aliases_update')

            # Text to add to aliases list file when creating new mailin list to
            # activate new list hanglind by mta 
            # You can use $LIST_NAME it would be substituted by list name
            if config.has_option('mailman', 'aliases_config'):
                self._aliases_config = config.get('mailman', 'aliases_config')

        # Path to mailman administrator scripts
        self._bin_dir = os.path.join(self._mailman_dir, 'bin/')

        self.listname = '{0}-{1}'.format(self._project.id, self._name)


        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n

        con = openDB()
        c = con.cursor()
        res = c.execute('select sha_password, email from users where login=%s limit 1', 
                (project.admin,))
        if not res:
            raise ScalakError("User given as admin don't exist in db")

        tmp = c.fetchone()

        adminPasswd = tmp[0]
        adminEmail = tmp[1]

        con.commit()
        c.close()


        # Mailman specific callbacks
        if Utils.list_exists(self.listname):
            raise ScalakError("Error: mailing list with given name {0} already " \
                    "exists".format(self.listname))

        urlhost = mm_cfg.DEFAULT_URL_HOST
        host_name = mm_cfg.VIRTUAL_HOSTS.get(urlhost, mm_cfg.DEFAULT_EMAIL_HOST)
        web_page_url = mm_cfg.DEFAULT_URL_PATTERN % urlhost

        mlist = MailList.MailList()

        # Part of code from Mailman:bin/newlist
        oldmask = os.umask(002)
        lang = mm_cfg.DEFAULT_SERVER_LANGUAGE
        try:
            try:
                try:
                    if lang == mm_cfg.DEFAULT_SERVER_LANGUAGE:
                        langs = [lang]
                    else:
                        langs = [lang, mm_cfg.DEFAULT_SERVER_LANGUAGE]
                    mlist.Create(self.listname, adminEmail, adminPasswd, langs=langs,
                                 emailhost=host_name)

                finally:
                    os.umask(oldmask)
            except Errors.BadListNameError, s:
                raise ScalakError('Illegal list name: %(s)s')
            except Errors.EmailAddressError, s:
                raise ScalakError('Bad owner email address: %(s)s.'  +
                        'Owner addresses need to be fully-qualified names, ' +
                        'like "owner@example.com", not just "owner".')
            except Errors.MMListAlreadyExistsError:
                raise ScalakError_('List already exists: %(listname)s')

            # Assign domain-specific attributes
            mlist.host_name = host_name
            mlist.web_page_url = web_page_url

            # And assign the preferred language
            mlist.preferred_language = lang

            mlist.Save()
        finally:
            mlist.Unlock()

        # Now do the MTA-specific list creation tasks
        if mm_cfg.MTA:
            modname = 'Mailman.MTA.' + mm_cfg.MTA
            __import__(modname)
            print "Please note mailing list emails"
            sys.modules[modname].create(mlist, quiet=True)

        self._newAliases()

        for user in project.getUsers():
            self.addUser(user[0], email=user[3])

    def _newAliases(self):
        """Takes template for trac.ini and save it filled up into project dir

            tracDir - path to trac instance
        """

        if not self._aliases_config:
            aliases = self._aliasesTpl
        else:
            aliases = Template(self._aliases_config)


        with open(self._aliases_file, 'a') as file:
            file.write(aliases.safe_substitute({'LIST_NAME' : self.listname}))

        # updating aliases list for new mailing list
        if self._runCommand([], self._aliases_update):
            raise ScalakError("Error while trying to update " \
                    "aliases list")


    def remove(self):
        """Deletes mailing list

        First delete list reference from mailman, then delete aliases from MTA
        """

        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n

        stdoutOld = sys.stdout
        sys.stdout = open('/dev/null', 'w')

        # Part from Mailman code (rmlist script)
        REMOVABLES = []
        if Utils.list_exists(self.listname):
            mlist = MailList.MailList(self.listname, lock=0)

            # Do the MTA-specific list deletion tasks
            if mm_cfg.MTA:
                modname = 'Mailman.MTA.' + mm_cfg.MTA
                __import__(modname)
                sys.modules[modname].remove(mlist)

            REMOVABLES = [
                (os.path.join('lists', self.listname), ('list info')),
                ]

            # Remove any stale locks associated with the list
            for filename in os.listdir(mm_cfg.LOCK_DIR):
                fn_listname = filename.split('.')[0]
                if fn_listname == self.listname:
                    REMOVABLES.append((os.path.join(mm_cfg.LOCK_DIR, filename),
                                       ('stale lock file')))
            for dirtmpl, msg in REMOVABLES:
                dir = os.path.join(mm_cfg.VAR_PREFIX, dirtmpl)
                if os.path.islink(dir):
                    os.unlink(dir)
                elif os.path.isdir(dir):
                    shutil.rmtree(dir)
                elif os.path.isfile(dir):
                    os.unlink(dir)


        with open(self._aliases_file, 'r') as tmp:
            file = tmp.readlines()

        with open(self._aliases_file, 'w') as tmp:
            for line in file:
                if(self.listname not in line):
                    tmp.write(line)

        sys.stdout.close()
        sys.stdout = stdoutOld

    def addUser(self, login, name = None, last_name = None, email = None, 
            passwd = None, sha_passwd = None, note = None):

        if not email:
            raise ScalakError("You have to supply user email.")


        # Some not really nice mailman hacks
        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        sitedir = os.path.join(sys.prefix, 'lib', 'python'+sys.version[:3],
                'site-packages')
        sys.path.append(sitedir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n
        from email.Utils import parseaddr

        class UserDesc: pass

        if not Utils.list_exists(self.listname):
            raise ScalakError("No such mailing list")

        mlist = MailList.MailList(self.listname)
        usr = UserDesc()
        usr.fullname, usr.address = parseaddr(email)
        usr.digest = 0
        try:
            mlist.ApprovedAddMember(usr, 0, 0)
            mlist.Save()
        finally:
            mlist.Unlock()

    def removeUser(self, id):

        con = openDB()
        c = con.cursor()
        res = c.execute('select email from users where login=%s limit 1', 
                (id,))
        if not res:
            raise ScalakError("Given user dosen't exists")

        email = c.fetchone()[0]
        con.commit()
        c.close()


        # Some not really nice mailman hacks
        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        sitedir = os.path.join(sys.prefix, 'lib', 'python'+sys.version[:3],
                'site-packages')
        sys.path.append(sitedir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n
        from email.Utils import parseaddr

        class UserDesc: pass

        if not Utils.list_exists(self.listname):
            raise ScalakError("No such mailing list")

        mlist = MailList.MailList(self.listname)
        usr = UserDesc()
        usr.fullname, usr.address = parseaddr(email)
        usr.digest = 0
        try:
            if mlist.isMember(email):
                mlist.ApprovedDeleteMember(email, 'bin/remove_members', 0, 0)
            mlist.Save()
        finally:
            mlist.Unlock()


registerService(Mailman._type, Mailman._subtype, Mailman)

#TESTS
class dummy_config():
    def get(self, a, b):
        if a == 'general' and b == 'projects_dir':
            return "/var/scalak/projects/"
        if a == 'trac' and b == 'plugins_dir':
            return "/var/scalak/trac_plugins"
            #return "/home/bulislaw/projects/"
        return ""
    def has_option(self, a, b):
        return False
    def has_section(self, a):
        return False

def testProject():
    proj = Project(dummy_config())
    proj._id = 'test'
    proj.admin = 'bulislaw'
    proj._description = 'brak'
    proj.create()
    return proj

def testTrac(proj):
    proj.addService(Trac())

def testSvn(proj, name = None):
    if name is not None:
        proj.addService(Subversion(name))
    else:
        proj.addService(Subversion())


def testHg(proj, name = None):
    if name is not None:
        proj.addService(Mercurial(name))
    else:
        proj.addService(Mercurial())

def testMailman(proj, name = None):
    if name is not None:
        proj.addService(Mailman(name))
    else:
        proj.addService(Mailman())

