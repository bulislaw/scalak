# -*- coding: utf8 -*-
#
# dbAuth Trac plugin
# Copyright 2010 Bartosz Szatkowski <bulislaw@linux.com>
# This file is part of Scalak

from trac.core import *
from trac.config import ExtensionOption, Option
from db import ScalakDB

try:
    from acct_mgr.api import IPasswordStore
    from acct_mgr.pwhash import IPasswordHashMethod
except ImportError:
    raise TracError("You need to install Trac Account Manager plugin")


class dbAuth(Component):
    """Data base based authorization module for Trac - to be used with account manager plugin"""
    
    implements(IPasswordStore)
    hash_method = ExtensionOption('account-manager', 'hash_method',
	    IPasswordHashMethod, 'HtDigestHashMethod')

    def __init__(self):
	"""Acquire db connection"""
	self._db = ScalakDB(self.compmgr)

    def get_users(self):
        """Returns an iterable of the known usernames"""

	result = self._db.execute(self._db.sql_get_users, (self._db.project_id,))
		       
	for user, in result:
	    yield user

 
    def has_user(self, user):
	result = self._db.execute(self._db.sql_has_user, (self._db.project_id, user))
	for row in result:
	    self.__close()
	    return True
	return False
 
    def set_password(self, user, password):
        """Changing password should be done by Scalak-admin or dashboard
        """
        raise TracError("Changing password should be done via dashboard, " \
                "new accounts should be created by Scalak administartor.")



    def check_password(self, user, password):
        """Checks if the password is valid for the user.
        """

	result = self._db.execute(self._db.sql_get_pass, 
                (user, self._db.project_id))

	for hash, in result:
	    return self.hash_method.check_hash(user, password, hash)

	return None

    def delete_user(self, user):
        """Deletes user from project
        Returns True if the account existed and was deleted, False otherwise.
        """

	if not self.has_user(user):
	    return False

	result = self._db.execute(self._db.sql_del_user, (user, self._db.project_id))
	return True

