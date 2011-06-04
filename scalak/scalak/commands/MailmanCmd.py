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
from scalak import Project, getClass
from scalak.utils import *

class MailmanCmd(common.Command):
    _command = "mailman"
    _man = """
mailman add [list-name]
    add mailing list to the project. Full list name would be 
    <project-name>-<list-name>, default list-name is devel.

mailman remove list-name
    removes mailing list from project (and system).
    Please note that full mailing name is <project-name>-<list-name> only
    second part should be given.
    """

    def execute(self, command, project_name, cl_args, config):
        super(MailmanCmd, self).execute(command, project_name, \
                cl_args, config)

        if len(cl_args) == 0:
            raise ScalakError("No subcommand specified.")

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
        type = getClass("mailing", "mailman")
        if not type:
            raise ScalakError("Mailman add: no such service type. Please contact" \
                    "Scalak administrator.")

        name = None
        if len(cl_args) > 1:
            name = cl_args[1]
        project.addService(type(name))

        print "List added"

    def remove(self, project, cl_args, config):
        if len(cl_args) != 2:
            raise ScalakError("No list name specified")

        name = cl_args[1]
        srv = project.getService("mailing", "mailman", name)
        if not srv or len(srv) < 1:
            raise ScalakError("Mailman add: no such mailing list for given " \
                    "project")

        project.delService(srv[0])

        print "List removed"

common.registerCommand(MailmanCmd._command, MailmanCmd())
