#!/usr/bin/env pyton
from trac.core import *

class DbDefaults(Component):
    """Defaults options values for db access
    
    Idea is to provide simple but flexible trac plugin for authorization
    via data base.

    SQL query Options: name - description - params
	sql_get_user - lists all users in project - project_id
	sql_has_user - returns user login if exists - user_login
	sql_user_in_project - returns all user data if he belongs to 
		project - project_id, user_login
	sql_new_user - adds user to project - user_login, project_id
	sql_get_pass - returns pass if user belong to project 
		- user_login, project_id
	sql_del_user - deletes user from given project - user_login
		, project_id
    Other:
	db_host - host with db to connect to
	db_name - database name
	db_user - database user
	db_pass - db_user password
    """

    #Base
    db_host = "localhost"
    db_name = "scalak"
    db_user = "scalak"
    db_pass = "scalak"

    #SQL - dbAuth
    sql_get_users = "select user from user_project where project=%s"
    sql_has_user = "select user from user_project where  project=%s \
            and user=%s limit 1"
    sql_user_in_project = "select * from user_project where user=%s \
		    and project=%s"
    sql_user_exists = "select * from users where login=%s limit 1"
    sql_get_pass = "select password from users, user_project, projects \
                    where login=%s and project=%s and login=user \
                    and projects.id=project and active=1 limit 1"
    sql_del_user = "delete from user_project where user=%s and \
		    project=%s"



