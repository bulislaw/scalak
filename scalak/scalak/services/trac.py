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

from string import Template
import os
import shutil
import MySQLdb as db
import stat

from trac.env import Environment as Env
from trac.db.api import with_transaction
from trac.perm import PermissionSystem

from scalak.utils import *
from scalak import Service, registerService

class Trac(Service):
    """Service integrating Scalak with Trac"""

    _type = "trac"
    _subtype = "trac"

    _dbSpec = "sqlite:db/trac.db"
    _command = "trac-admin"
    _tracConfig = os.path.join(os.path.dirname(__file__),
            "templates/trac/trac.ini.template")
    _apacheConfig = os.path.join(os.path.dirname(__file__),
            "templates/trac/trac.conf")

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

