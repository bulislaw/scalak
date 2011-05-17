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

import getopt
import time
import datetime

import scalak.commands.common as common
from scalak.project import *
from scalak.utils import *

class ProjectCmd(common.Command):
    _command = "create", "remove"
    _man = """
create [-b brief] [-d description] [-e due_date] admin
    Creates complete, raw Scalak environment. Just directory structure with trac and www.
    admin - must be existing user id.
    brief - short description
    description - long description
    due_date - date like 'RRRR-MM-DD'

remove
    (DANGER) Removes project and all its services. BE CAREFUL
    """
    admin = None
    brief = None
    desc = None
    due = None

    def execute(self, command, project_name, cl_args, config):
        """Runs action connected with given command
        
        command - string, command
        project_name - string, name of project to create
        loose - list, loose arguments
        args - dict (str,str) of supplied arguments
        """

        if command == "create":
            self.create(command, project_name, cl_args, config)
        elif command == "remove":
            self.remove(project_name, config)
        else:
            return -1

        return 0

    def remove(self, project_name, config):
        p = Project()
        p.load(project_name, config)
        p.remove()

    def create(self, command, project_name, cl_args, config):
        args,loose = getopt.getopt(cl_args, 'b:d:e:')
        args = dict(args)

        if len(loose) < 1:
            raise ScalakError("Create Error: at last administrators id must be supplied")

        admin = loose[0]
        brief = args.get('-b', None)
        desc = args.get('-d', None)

        # TODO checking date format
        due = args.get('-e', None)
        today = datetime.date.today().isoformat()

        project = Project(config, project_name, admin, date, due, brief, desc)
        project.create()
        project.addService(Trac())
        project.addUser(admin)

common.registerCommand(ProjectCmd._command, ProjectCmd())
