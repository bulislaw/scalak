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
from scalak import Project
from scalak.utils import *

class UserCmd(common.Command):
    _command = "user"
    _man = """
user add <login>
    add existing user to project

user remove <login>
    remove user from project
    """

    def execute(self, command, project_name, cl_args, config):
        super(UserCmd, self).execute(command, project_name, \
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
            raise ScalakError("User add: You have to supply user id")

        id = cl_args[1]
        if not findUser(id):
            raise ScalakError("User add: user dosen't exists")

        project.addUser(id)

        print "User added"

    def remove(self, project, cl_args, config):
        if len(cl_args) < 2:
            raise ScalakError("User add: You have to supply user id")

        id = cl_args[1]
        if not findUser(id, project.id):
            raise ScalakError("User remove: user dosen't exists or not " \
                    "member of the project")

        project.removeUser(id)

        print "User removed"


common.registerCommand(UserCmd._command, UserCmd())

