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

from subprocess import call
import os
import shutil
import MySQLdb as db
from time import sleep
import sys

from scalak.utils import *

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
