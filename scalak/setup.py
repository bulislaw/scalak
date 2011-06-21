#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name = "Scalak",
    version = "0.2",
    description = "Integrated project management envirionment",
    author = "Bartosz Szatkowski",
    author_email = "bulislaw@linux.com",
    license = "GPL 3+",
    packages=["scalak", "scalak/commands", "scalak/services"],
    package_data={"scalak" : ["templates/*.conf", "templates/svn/*",
            "templates/hg/*", "templates/trac/*"]},
    scripts=["scalak-admin", "scalak-users", "scalak-info"],
    data_files=[("/etc/", ["scalak.conf"]),
                ("/usr/sbin", ["scalak-ftp-auth",
			"scalak-remote-api"])]
)
