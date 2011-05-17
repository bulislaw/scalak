#!/usr/bin/env python
#
# Scalak Trac Plugin
# Copyright 2010 Bartosz Szatkowski <bulislaw@linux.com>
#

from setuptools import setup

setup(
    name = 'ScalakTracPlugin',
    version = '0.2',
    author = 'Bartosz Szatkowski',
    author_email = 'bulislaw@linux.com',
    url = 'http://scalak.ics.p.lodz.pl',
    description = 'Scalak Trac plugin provide Trac integration with Scalak \
	    - complete integrated programming environment.',
    license = 'GPL 3.0+',
    zip_safe=True,
    packages=['scalaktrac'],
    install_requires = [
	'trac>=0.12',
	'TracAccountManager>0.2.0',
	],
    entry_points = {
        'trac.plugins': [
	    'scalaktrac.defaults = scalaktrac.defaults',
	    'scalaktrac.db = scalaktrac.db',
            'scalaktrac.auth = scalaktrac.auth',
        ]
    },
)
