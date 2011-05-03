#!/bin/bash

wwwusr=www-data
wwwgrp=www-data

# For now its hard to move Scalak to other folder,
# if You would like to do that anyway, You should change
# /var/scalak in many places in config files
mkdir -p /var/scalak/projects
mkdir -p /var/scalak/python_egg_cache
mkdir -p /var/scalak/trac_plugins

cp conf/scalakweb.wsgi /var/scalak/

pushd scalak
python setup.py install
popd

pushd scalak-trac-plugin/
python setup.py install
popd

pushd scalakweb/scalakweb
python setup.py install
popd

cp -r scalakweb/scalakweb /var/scalak

chown -R $wwwusr:$wwwgrp /var/scalak/* 