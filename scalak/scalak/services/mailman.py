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
import sys

from scalak.utils import *
from scalak import registerService, Service

class Mailman(Service):
    """Mailing list suport for Scalak

    Mailman module is hard one - Mailman don't have extensive cli scripts,
    so i have to use some internal mechanisms 
    """

    _type = "mailing"
    _subtype = "mailman"

    _command = None

    _mailman_dir = '/usr/lib/mailman/'
    _aliases_config = None
    _aliases_file = '/etc/aliases'
    _aliases_update = 'newaliases'

    _aliasesTpl = Template("""
$LIST_NAME:              "|/var/lib/mailman/mail/mailman post mailman"
$LIST_NAME-admin:        "|/var/lib/mailman/mail/mailman admin mailman"
$LIST_NAME-bounces:      "|/var/lib/mailman/mail/mailman bounces mailman"
$LIST_NAME-confirm:      "|/var/lib/mailman/mail/mailman confirm mailman"
$LIST_NAME-join:         "|/var/lib/mailman/mail/mailman join mailman"
$LIST_NAME-leave:        "|/var/lib/mailman/mail/mailman leave mailman"
$LIST_NAME-owner:        "|/var/lib/mailman/mail/mailman owner mailman"
$LIST_NAME-request:      "|/var/lib/mailman/mail/mailman request mailman"
$LIST_NAME-subscribe:    "|/var/lib/mailman/mail/mailman subscribe mailman"
$LIST_NAME-unsubscribe:  "|/var/lib/mailman/mail/mailman unsubscribe mailman" 
""")


    def __init__(self, name = None):
        """Name is only part of real list name - full name is <project-name>-<name>-<list-spec>"""

        self._name = "devel"
        if name:
            self._name = name



    def _initPath(self):
        Utils.list_exists("test")


    def _serialize(self):
        """Returns valuese needed to be serialized to data base

        Return:
            list of tuples (key, value)
        """

        return [('_mailman_dir', self._mailman_dir), 
                ('_aliases_file', self._aliases_file),
                ('_aliases_update', self._aliases_update),
                ('_aliases_config', self._aliases_config)]


    def load(self, project, name, values):
        """Loads Trac service object from values

        Arg:
            values - list of tuples ('name', value)
        """

        self._name = name
        self._project = project
        for v in values:
            setattr(self, v[0], v[1])
        self.listname = '{0}-{1}'.format(self._project.id, self._name)
        self._bin_dir = os.path.join(self._mailman_dir, 'bin/')


    def deploy(self, project, config):
        """Creates and connect mailman instance with Scalak

        This part is kind of tricky because mailman provide minimal cli
        interface, that is definitely not sufficient.


        Parameters:
            project - Project instance (service would be added to it)
            config - ConfigParser.SafeconfigParser

        Complications:
            Mailman is using SHA-digested passwords, Scalak (mostly because
                of Apache) htpasswd. Most basic (and currently used) method
                to supply the SHA password is to keep it in db (they are
                generated with htpasswd)

        Steps:
            * Reading configuration for mailman bin directory, aliases, alias
                update command
            * Reading sha admin password (scalak keeps passwords in htpasswd
                mainly because of apache, so i add additional field with sha
                passwd)
            * Then is kind of black box - mailman internal callbacks, used
                code from Mailman:bin/newlist
            * Configuration part - adding and updating aliases
        """

        super(Mailman, self).deploy(project, config)

        if self._config.has_section('mailman'):
            # Path to mailman install directory
            if config.has_option('mailman', 'mailman_dir'):
                self._mailman_dir = config.get('mailman', 'mailman_dir')


            # Path to mta aliases file
            if config.has_option('mailman', 'aliases_file'):
                self._aliases_file = config.get('mailman', 'aliases_file')

            # Command tu update aliases list
            if config.has_option('mailman', 'aliases_update'):
                self._aliases_update = config.get('mailman', 'aliases_update')

            # Text to add to aliases list file when creating new mailin list to
            # activate new list hanglind by mta 
            # You can use $LIST_NAME it would be substituted by list name
            if config.has_option('mailman', 'aliases_config'):
                self._aliases_config = config.get('mailman', 'aliases_config')

        # Path to mailman administrator scripts
        self._bin_dir = os.path.join(self._mailman_dir, 'bin/')

        self.listname = '{0}-{1}'.format(self._project.id, self._name)


        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n

        con = openDB()
        c = con.cursor()
        res = c.execute('select sha_password, email from users where login=%s limit 1', 
                (project.admin,))
        if not res:
            raise ScalakError("User given as admin don't exist in db")

        tmp = c.fetchone()

        adminPasswd = tmp[0]
        adminEmail = tmp[1]

        con.commit()
        c.close()


        # Mailman specific callbacks
        if Utils.list_exists(self.listname):
            raise ScalakError("Error: mailing list with given name {0} already " \
                    "exists".format(self.listname))

        urlhost = mm_cfg.DEFAULT_URL_HOST
        host_name = mm_cfg.VIRTUAL_HOSTS.get(urlhost, mm_cfg.DEFAULT_EMAIL_HOST)
        web_page_url = mm_cfg.DEFAULT_URL_PATTERN % urlhost

        mlist = MailList.MailList()

        # Part of code from Mailman:bin/newlist
        oldmask = os.umask(002)
        lang = mm_cfg.DEFAULT_SERVER_LANGUAGE
        try:
            try:
                try:
                    if lang == mm_cfg.DEFAULT_SERVER_LANGUAGE:
                        langs = [lang]
                    else:
                        langs = [lang, mm_cfg.DEFAULT_SERVER_LANGUAGE]
                    mlist.Create(self.listname, adminEmail, adminPasswd, langs=langs,
                                 emailhost=host_name)

                finally:
                    os.umask(oldmask)
            except Errors.BadListNameError, s:
                raise ScalakError('Illegal list name: %(s)s')
            except Errors.EmailAddressError, s:
                raise ScalakError('Bad owner email address: %(s)s.'  +
                        'Owner addresses need to be fully-qualified names, ' +
                        'like "owner@example.com", not just "owner".')
            except Errors.MMListAlreadyExistsError:
                raise ScalakError_('List already exists: %(listname)s')

            # Assign domain-specific attributes
            mlist.host_name = host_name
            mlist.web_page_url = web_page_url

            # And assign the preferred language
            mlist.preferred_language = lang

            mlist.Save()
        finally:
            mlist.Unlock()

        # Now do the MTA-specific list creation tasks
        if mm_cfg.MTA:
            modname = 'Mailman.MTA.' + mm_cfg.MTA
            __import__(modname)
            print "Please note down mailing list emails (You DON'T have to " \
                    "add this aliases manually to /etc/aliases)"
            sys.modules[modname].create(mlist, quiet=True)

        self._newAliases()

        for user in project.getUsers():
            self.addUser(user[0], email=user[3])

    def _newAliases(self):
        """Takes template for trac.ini and save it filled up into project dir

            tracDir - path to trac instance
        """

        if not self._aliases_config:
            aliases = self._aliasesTpl
        else:
            aliases = Template(self._aliases_config)


        with open(self._aliases_file, 'a') as file:
            file.write(aliases.safe_substitute({'LIST_NAME' : self.listname}))

        # updating aliases list for new mailing list
        if self._runCommand([], self._aliases_update):
            raise ScalakError("Error while trying to update " \
                    "aliases list")


    def remove(self):
        """Deletes mailing list

        First delete list reference from mailman, then delete aliases from MTA
        """

        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n

        stdoutOld = sys.stdout
        sys.stdout = open('/dev/null', 'w')

        # Part from Mailman code (rmlist script)
        REMOVABLES = []
        if Utils.list_exists(self.listname):
            mlist = MailList.MailList(self.listname, lock=0)

            # Do the MTA-specific list deletion tasks
            if mm_cfg.MTA:
                modname = 'Mailman.MTA.' + mm_cfg.MTA
                __import__(modname)
                sys.modules[modname].remove(mlist)

            REMOVABLES = [
                (os.path.join('lists', self.listname), ('list info')),
                ]

            # Remove any stale locks associated with the list
            for filename in os.listdir(mm_cfg.LOCK_DIR):
                fn_listname = filename.split('.')[0]
                if fn_listname == self.listname:
                    REMOVABLES.append((os.path.join(mm_cfg.LOCK_DIR, filename),
                                       ('stale lock file')))
            for dirtmpl, msg in REMOVABLES:
                dir = os.path.join(mm_cfg.VAR_PREFIX, dirtmpl)
                if os.path.islink(dir):
                    os.unlink(dir)
                elif os.path.isdir(dir):
                    shutil.rmtree(dir)
                elif os.path.isfile(dir):
                    os.unlink(dir)


        with open(self._aliases_file, 'r') as tmp:
            file = tmp.readlines()

        with open(self._aliases_file, 'w') as tmp:
            for line in file:
                if(self.listname not in line):
                    tmp.write(line)

        sys.stdout.close()
        sys.stdout = stdoutOld

    def addUser(self, login, name = None, last_name = None, email = None, 
            passwd = None, sha_passwd = None, note = None):

        if not email:
            raise ScalakError("You have to supply user email.")


        # Some not really nice mailman hacks
        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        sitedir = os.path.join(sys.prefix, 'lib', 'python'+sys.version[:3],
                'site-packages')
        sys.path.append(sitedir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n
        from email.Utils import parseaddr

        class UserDesc: pass

        if not Utils.list_exists(self.listname):
            raise ScalakError("No such mailing list")

        mlist = MailList.MailList(self.listname)
        usr = UserDesc()
        usr.fullname, usr.address = parseaddr(email)
        usr.digest = 0
        try:
            mlist.ApprovedAddMember(usr, 0, 0)
            mlist.Save()
        finally:
            mlist.Unlock()

    def removeUser(self, id):

        con = openDB()
        c = con.cursor()
        res = c.execute('select email from users where login=%s limit 1', 
                (id,))
        if not res:
            raise ScalakError("Given user dosen't exists")

        email = c.fetchone()[0]
        con.commit()
        c.close()


        # Some not really nice mailman hacks
        # Need to import Mailman code 
        sys.path.insert(0, self._mailman_dir)
        sitedir = os.path.join(sys.prefix, 'lib', 'python'+sys.version[:3],
                'site-packages')
        sys.path.append(sitedir)
        from Mailman import mm_cfg
        from Mailman import MailList
        from Mailman import Utils
        from Mailman import Errors
        from Mailman import Message
        from Mailman import i18n
        from email.Utils import parseaddr

        class UserDesc: pass

        if not Utils.list_exists(self.listname):
            raise ScalakError("No such mailing list")

        mlist = MailList.MailList(self.listname)
        usr = UserDesc()
        usr.fullname, usr.address = parseaddr(email)
        usr.digest = 0
        try:
            if mlist.isMember(email):
                mlist.ApprovedDeleteMember(email, 'bin/remove_members', 0, 0)
            mlist.Save()
        finally:
            mlist.Unlock()

registerService(Mailman._type, Mailman._subtype, Mailman)
