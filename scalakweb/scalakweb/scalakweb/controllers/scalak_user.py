import logging
from urlparse import urlparse

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scalakweb.lib.base import BaseController, render
import scalakweb.lib.helpers as h

from webhelpers.html.tags import link_to
from webhelpers.html.tools import mail_to
import webhelpers.html.builder as html

from scalak.utils import *
from scalak.project import *

import authkit
import authkit.authenticate
from authkit.authorize.pylons_adaptors import authorize, authorized
from authkit.permissions import ValidAuthKitUser, RemoteUser

log = logging.getLogger(__name__)

def genMenu(page):
        menu = []

        m = h.MenuItem("User informations", url(controller="scalak_user", \
                action="userInfo"))
        m.addSubitem("Edit", url(controller="scalak_user", \
                action="userInfoEdit"))
        menu.append(m)

        m = h.MenuItem("Projects", url(controller="scalak_user", \
                action="projects"))
        m.addSubitem("Administration", url(controller="scalak_user", \
                action="myProjects"))
        m.addSubitem("Join", url(controller="scalak_user", \
                action="join"))
        menu.append(m)

        m = h.MenuItem("Logout", url(controller="scalak_user", \
                action="logout"))
        menu.append(m)

        return menu

def checkLogIn(session):
    if not session.get("user_id", None) or \
            not authorized(RemoteUser()):
        redirect(url(controller="scalak_user", action="login"))

class ScalakUserController(BaseController):

    def login(self):
	if not authorized(RemoteUser()):
            response.status = "401 Not authenticated"
            return "Only project administrator may view this page. " \
                    "Please try again."

        session['user_id'] = request.environ.get("REMOTE_USER")
        session.save()
        redirect(url(controller="scalak_user", action="userInfo"))

    def logout(self):
        session.clear()
        session.save()
        redirect(url(controller="auth", action="logout"))

    def userInfo(self):
        checkLogIn(session)

        c.site = "Projects"
        c.name = session['user_id']
        c.menu = genMenu(self)

        res = getUserData(c.name)

        c.lineData = [("Username", res[0]), ("Name", res[1]),
                ("Last name", res[2]), ("Email", res[3])]

        c.content = render("/line_by_line.html") + html.literal("<br />")

        c.header = ["All my projects"]

        proj = userProjects(c.name)

        c.rows = []
        for x in proj:
            url_old = urlparse(request.url)
            url = url_old.scheme +'://' + url_old.netloc + getProjectUrl(x[0])
            c.rows.append((link_to(x[0], url),))

        c.style = "width:70%; text-align: left" #XXX: move css to templates

        c.content += render("/table.html")

        con.close()

        return render("/temp.html")

    def projects(self):
        checkLogIn(session)

        c.site = "User information"
        c.name = session['user_id']
        c.menu = genMenu(self)

        c.header = ["All my projects"]

        proj = getProjects(c.name)

        c.rows = []
        for x in proj:
            url_old = urlparse(request.url)
            url = url_old.scheme +'://' + url_old.netloc + getProjectUrl(x[0])
            c.rows.append((link_to(x[0], url),))

        c.style = "width:70%; text-align: left"

        c.content = render("/table.html")

        return render("/temp.html")

    def myProjects(self):
        checkLogIn(session)

        c.site = "Projects"
        c.name = session['user_id']
        c.menu = genMenu(self)

        c.header = ["Projects belong to me"]

        #XXX get user admin projects

        c.rows = []
        for x in getOwnedProject(c.name):
            url_old = urlparse(request.url)
            url = url_old.scheme +'://' + url_old.netloc + getProjectUrl(x[0])
            c.rows.append((link_to(x[0], url),))

        c.style = "width:70%; text-align: left" #XXX css to templates

        c.content = render("/table.html")

        return render("/temp.html")

    def join(self):
        checkLogIn(session)

        c.site = "Join"
        c.name = session['user_id']
        c.menu = genMenu(self)

        c.content = render("/join.html")

        return render("/temp.html")

    def joinSubmit(self):
        checkLogIn(session)
        c.name = session['user_id']

        res = findUser(request.params['project_id'], c.name)

        if res:
            h.flash("User is already project member")
            redirect(url(controller="scalak_user", action="join"))

        if not Project.projectExists(request.params['project_id']):
            h.flash("Project doesn't exists")
            redirect(url(controller="scalak_user", action="join"))

        res = getUserRequests(c.name, request.params['project_id'])
        if res:
            h.flash("Your request already awaiting acceptance")
            redirect(url(controller="scalak_user", action="join"))

        addUserRequest(c.name, request.params['project_id']))

        h.flash("Your request has been send")
        redirect(url(controller="scalak_user", action="userInfo"))

