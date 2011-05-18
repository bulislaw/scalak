#!/usr/bin/env python

from trac.core import *
from trac.config import ExtensionOption, Option
from scalak import utils

from defaults import DbDefaults

try:
    import MySQLdb as db
except:
    raise TracError("You need MySQLdb lib")	


class ScalakDB(Component):
    """Data base access moudle for Scalak environement (in fact any kind \
	    of MySQL database would do). Designed to be as flexible as \
	    possible
    
    Data base schema is kind of fuzzy for now so ive decide to use non
    normal form etc. but more flexible.

    Tables (as far as seen from this plugin):
	* users:
	    - login (text)
	    - keyf (text)
		+ pass, email, name, last_name, index_num
	    - value (text)
	* user_project:
	    - user (text) ref. users.login
	    - project (text) ref. projects.id
    """

    def _die(self, msg=None):
	if msg is None:
	    msg = "Project ID is not definded, contact Scalak admin."
	raise TracError(msg)

    def __init__(self):
	self.error = None
	self.project_id = self.env.config.get("scalak", "project_id")
	if not self.project_id:
	    self.error = True
	    self._die()

	#sql queries - maybe someday, someone would change queries 
	#   this is very simple and straightforward way

	self.sql_get_users = self.env.config.get("scalak", "sql_get_users",
		DbDefaults.sql_get_users)
	self.sql_has_user = self.env.config.get("scalak", "sql_has_user",
		DbDefaults.sql_has_user)
	self.sql_has_user = self.env.config.get("scalak", "sql_has_user",
		DbDefaults.sql_has_user)
	self.sql_user_in_project = self.env.config.get("scalak", 
		"sql_user_in_project", DbDefaults.sql_user_in_project)
	self.sql_user_exists = self.env.config.get("scalak", 
		"sql_user_exists", DbDefaults.sql_user_exists)
	self.sql_get_pass = self.env.config.get("scalak", "sql_get_pass",
		DbDefaults.sql_get_pass)
	self.sql_del_user = self.env.config.get("scalak", "sql_del_user",
		DbDefaults.sql_del_user)


	__con = None

    def __connect(self):
	"""Connect to a database and returns a cursor"""
	if self.error is not None:
	    self._die()
	    return -1

	self.__con = utils.openDB()
	self.__c = self.__con.cursor()

	return self.__c

    def __close(self):
	"""Commits the changes and closes the cursor"""
	self.__con.commit()
	self.__c.close()

    def execute(self, sql, param):
	"""Bind params to sql and execute it
	
	Params:
	    sql : string, sql query
	    param : list, params to be bind to sql
	"""
	if self.error is not None:
	    self.__die__()
	res = None

	try:
	    self.__connect()
	    cursor = self.__connect()

	    cursor.execute(sql, param)
	    res = cursor.fetchall()

	except db.DatabaseError as (errno, errtxt):
	    self._die("Database error: {0} : {1}".format(errno, errtxt))

	finally:
	    self.__close()
	return res

