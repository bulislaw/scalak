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

__commands__ = {}
__handlers__ = []

def registerCommand(command, cls):
    """Each class that wants to provide command needs to run this
    
    command - single command as string (eg "reset") or list of strings
    cls - class (subclass of Command) connected with command(s)

    Scalak-admin would import all class from given module and 'source it' so
    user may add plugins (in fairly easy way), just droping file int
    <path to scalak>/commands
    """
    global __commands__, __handlers__
    if not isinstance(cls, Command):
        return

    __handlers__.append(cls)

    if isinstance(command, str):
        cmd = __commands__.get(command, [])
        cmd.append(cls)
        __commands__[command] = cmd
    else:
        for tmpcmd in command:
            cmd = __commands__.get(tmpcmd, [])
            cmd.append(cls)
            __commands__[tmpcmd] = cmd


class Command(object):
    """Common parent for all classes provaiding commands for scalak-admin"""

    _command = None
    _man = None

    def execute(self, command, project_name, cl_args, config):
        pass

    def man(self):
        return self._man
