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

from scalak.utils import *
from scalak.services import Repository
from scalak import registerService

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
