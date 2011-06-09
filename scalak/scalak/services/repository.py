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

import shutil

from scalak.utils import *
from scalak import Service

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

        trac = self._project.getService("trac")
        if len(trac):
            trac[0].addRepository(self._name, self._repoPath, self._subtype)
        else:
            raise ScalakError("There is no Trac instance for given project."
                    " Contact Scalak administrator.")

    def _disconnectTrac(self):
        """Connects repository to Trac"""

        trac = self._project.getService("trac")
        if len(trac):
            trac[0].delRepository(self._name)
        else:
            raise ScalakError("There is no Trac instance for given project."
                    " Contact Scalak administrator.")

    def remove(self):
        self._disconnectTrac()
        shutil.rmtree(self._repoPath)
