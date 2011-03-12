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

import scalak.commands.common as common
from scalak.project import *
from scalak.utils import *

class RepositoryCmd(common.Command):
    _command = "repository"
    _man = """
repository add type [name]
    add repository to project and connect it to trac. Repository type may
    be: svn, hg. Default name is <repository-type><no> eg. svn0

repository remove type name
    (DANGER) removes repository from project and SYSTEM. Please use with caution.
    """

    def execute(self, command, project_name, cl_args, config):
        super(RepositoryCmd, self).execute(command, project_name, \
                cl_args, config)

        if len(cl_args) == 0:
            raise ScalakError("No subcommand specified")

        project = Project()
        project.load(project_name, config)

        if cl_args[0] == "add":
            self.add(project, cl_args, config) 
        elif cl_args[0] == "remove":
            self.remove(project, cl_args, config) 
        else:
            return -1

        return 0

    def add(self, project, cl_args, config):
        if len(cl_args) < 2:
            raise ScalakError("Repository add: You have to supply repository " \
                    "type")

        type = getClass("repository", cl_args[1])
        if not type:
            raise ScalakError("Repository add: no such repository type")

        name = None
        if len(cl_args) > 2:
            name = cl_args[2]

        project.addService(type(name))

        print "Repository added"

    def remove(self, project, cl_args, config):
        if len(cl_args) < 3:
            raise ScalakError("Repository remove: You have to supply repository " \
                    "type and name")

        name = cl_args[2]
        type = cl_args[1]
        srv = project.getService("repository", type, name)
        if not srv:
            raise ScalakError("Repository add: no such repository for given " \
                    "project")

        project.delService(srv[0])

        print "Repository removed"

common.registerCommand(RepositoryCmd._command, RepositoryCmd())

