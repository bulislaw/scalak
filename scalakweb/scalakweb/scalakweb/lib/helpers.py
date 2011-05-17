"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from pylons import url
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.html.tags import *

flash = _Flash()

class MenuItem():
    def __init__(self, name, link):
        self.name = name
        self.link = link

        self.sub = []

    def addSubitem(self, name, link):
        self.sub.append(MenuItem(name, link))

    def getMenu(self):
        return self.sub
