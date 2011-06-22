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

import os
import shutil
import stat
from pkg_resources import resource_filename
from string import Template

from scalak.project import registerService
from repository import Repository
from scalak.utils import *

class Mercurial(Repository):

    _subtype = "hg"
    _command = "hg"

    _apacheConfig =  resource_filename("scalak", 'templates/hg/hg.conf')
    _hgConfig =  resource_filename("scalak", "templates/hg/hgweb.config")
    _hgCgi =  resource_filename("scalak", 'templates/hg/hgwebdir.cgi')

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
            shutil.copy2(resource_filename('scalak',
                        'templates/hg/hgwebdir.cgi'),
                    os.path.join(self._hgPath, 'hgwebdir.cgi'))
            os.chmod(os.path.join(self._hgPath, 'hgwebdir.cgi'),
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                    stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH |
                    stat.S_IXOTH)

        shutil.copy2(resource_filename('scalak', 'templates/hg/hgrc'),
                os.path.join(self._repoPath, '.hg'))

registerService(Mercurial._type, Mercurial._subtype, Mercurial)
