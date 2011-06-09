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

pushd /tmp
svn co http://svn.edgewall.com/repos/trac/plugins/0.12/mercurial-plugin
cd mercurial-plugin
python setup.py install
cd ..
rm -rf mercurial-plugin
popd

cp -r scalakweb/scalakweb /var/scalak

pushd /var/scalak/scalakweb
easy_install ScalakWeb
paster setup-app production.ini
popd

chown -R $wwwusr:$wwwgrp /var/scalak/* 

/etc/init.d/apache2 restart
