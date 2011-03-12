import logging
from functools import wraps

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scalakweb.lib.base import BaseController, render
import scalakweb.lib.helpers as h

from webhelpers.html.tags import link_to
from webhelpers.html.tools import mail_to

from scalak.utils import *
from scalak.project import *

import authkit
import authkit.authenticate
from authkit.authorize.pylons_adaptors import authorize, authorized
from authkit.permissions import ValidAuthKitUser, RemoteUser

log = logging.getLogger(__name__)

def genMenu(page):
        menu = []

        m = h.MenuItem("Project informations", url(controller="project", \
                action="projectInfo"))
        m.addSubitem("Edit", url(controller="project", \
                action="projectInfoEdit"))
        menu.append(m)

        m = h.MenuItem("Users", url(controller="project", \
                action="users"))
        m.addSubitem("Add", url(controller="project", \
                action="userAdd"))
        m.addSubitem("Requests", url(controller="project", \
                action="usersRequests"))
        menu.append(m)

        m = h.MenuItem("Services", url(controller="project", \
                action="services"))

        m = h.MenuItem("Logout", url(controller="project", \
                action="logout"))
        menu.append(m)

        return menu

def checkLogin():
    if not session.get("project_id", None) or \
            not authorized(RemoteUser()):
        redirect(url(controller="auth", action="logout"))

class ProjectController(BaseController):

    def login(self, id=None):
        if not id:
            return "<h1>Please log in first.</h1>"

	if not authorized(RemoteUser()) or \
	        request.environ.get("REMOTE_USER") != getAdmin(id):
            response.status = "401 Not authenticated"
            return "Only project administrator may view this page. " \
                    "Please try again."

        session['project_id'] = id
        session.save()
        redirect(url(controller="project", action="projectInfo"))

    def logout(self):
        session.clear()
        session.save()
	redirect(url(controller="auth", action="logout"))

    def projectInfoEdit(self):
        checkLogin()

        c.site = "Project information edit"
        c.name = session['project_id']
        c.menu = genMenu(self)

        p = Project()
        p.load(c.name, getConfig())
        c.admin = p.admin
        c.create_date = p.create_date
        c.due_date = p.due_date
        c.brief = p.brief
        c.description = p.description

        c.content = render("/edit_project.html")

        return render("/temp.html")

    def projectInfoEditSubmit(self):
        checkLogin()

        c.name = session['project_id']

        p = Project()
        p.load(c.name, getConfig())
        p.brief = request.params['brief'].encode('utf-8')
        p.description = request.params['description'].encode('utf-8')

        h.flash("Information changed.")
        redirect(url(controller="project", action="projectInfo"))

    def projectInfo(self):
        checkLogin()

        c.site = "Project administration"
        c.name = session['project_id']
        c.menu = genMenu(self)

        p = Project()
        p.load(c.name, getConfig())
        c.lineData = [("Project name", p.id), ("Project Administrator", p.admin),
                ("Creation date", p.create_date), ("Due date", p.due_date),
                ("Brief info", p.brief), ("Description", p.description)]

        c.content = render("/line_by_line.html")

        return render("/temp.html")

    def users(self):
        checkLogin()

        c.site = "User administration"
        c.name = session['project_id']
        c.menu = genMenu(self)

        p = Project()
        p.load(c.name, getConfig())
        c.header = ('Login', 'EMail', "Remove?")

        c.rows = [(x[0], mail_to(x[3]), link_to("Remove", \
                url(controller="project", action='userRemove', id = x[0]), \
                confirm="Are You sure?")) \
                for x in p.getUsers()]

        c.style = "width: 70%; text-align: center;"

        c.content = render("/table.html")

        return render("/temp.html")

    def userRemove(self, id):
        checkLogin()

        c.name = session['project_id']
        p = Project()
        p.load(c.name, getConfig())
        try:
            p.removeUser(id)
        except ScalakError as err:
            h.flash("Error: {0}".format(err.value))
            redirect(url(controller="project", action="users"))

        h.flash("User '{0}' deleted.".format(id))
        redirect(url(controller="project", action="users"))

    def userAdd(self):
        checkLogin()

        c.site = "User add"
        c.name = session['project_id']
        c.menu = genMenu(self)
        c.content = render("/add_user.html")

        return render("/temp.html")

    def userAddSubmit(self):
        checkLogin()

        c.name = session['project_id']

        p = Project()
        p.load(c.name, getConfig())

        try:
            p.addUser(request.params['user_login'])
        except ScalakError as err:
            h.flash("Error: {0}".format(err))
            redirect(url(controller="project", action="userAdd"))

        h.flash("User added.")
        redirect(url(controller="project", action="userAdd"))

    def usersRequests(self):
        checkLogin()

        c.site = "User requests"
        c.name = session['project_id']
        c.menu = genMenu(self)

        p = Project()
        p.load(c.name, getConfig())
        c.header = ('Login', 'EMail', 'Accept as member', "Decline")

        c.rows = [(x[0], mail_to(x[1]), link_to("Accept", \
                url(controller="project", action='requestAccept', id = x[0])), \
                link_to("Decline", \
                url(controller="project", action='requestDecline', id = x[0]))) \
                for x in p.getRequests()]

        c.style = "width: 70%; text-align: center;"

        c.content = render("/table.html")

        return render("/temp.html")

    def requestAccept(self, id):
        checkLogin()

        c.name = session['project_id']

        p = Project()
        p.load(c.name, getConfig())

        p.setRequest(id, True)

        h.flash("User request accepted.")

        redirect(url(controller="project", action="usersRequests"))

    def requestDecline(self, id):
        checkLogin()

        c.name = session['project_id']

        p = Project()
        p.load(c.name, getConfig())

        p.setRequest(id, False)

        h.flash("User request declined.")

        redirect(url(controller="project", action="usersRequests"))

