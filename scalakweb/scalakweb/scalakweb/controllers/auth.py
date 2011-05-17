import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from scalakweb.lib.base import BaseController, render

log = logging.getLogger(__name__)

class AuthController(BaseController):

    def logout(self):
        return "<h1>You have been logged out.</h1>"


