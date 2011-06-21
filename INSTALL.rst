========================
Scalak Installation Guide
========================

INSTALL
-------
    - Apache2 (some reasonable new version)
    - libaprutil1-dbd-mysql (for authn_dbd Apache mod)
    - libapache2-mod-wsgi
    - libapache2-mod-python
    - MySQL server
    - python-mysqldb (Python MySQL DB-API lib)
    - Trac 0.12+
    - TrackAccoundManager plugin for Trac
    - Subversion
    - libapache2-svn
    - Mercurial
    - Pylons
    - Authkit
    - PureFTPd
    - RabbitMQ server
    - Pika

Configuration
-------------

1) Apache
   - Copy /etc/apache2/mods-available/authn_dbd.load to /etc/apache2/mods-enabled
   - Copy /etc/apache2/mods-available/dbd.load to /etc/apache2/mods-enabled
   - Copy conf/dbd.conf *(tweaking may be necessary)* to /etc/apache2/mods-enabled
   - Copy conf/scalak.conf to /etc/apache2/conf.d and make sure its executed
     *Note: there should be "Include /etc/apache2/conf.d/" somewhere in apache2.conf*

2) MySQL
   - Execute db/create.sql as MySQL root *(Note; be aware that for now there is no
        automatic way to change db user data, if You want to change default ones
        -- and its strongly recommended -- You have to change user data in 
        /etc/apache2/mods-enabled/dbd.conf and in python code)* #XXX

3) Check, personalize and run bootstrap.sh:
   # ./bootstrap.sh

4) Add following to autostart (/etc/rc.local or /etc/local.d/scalak.start
   or whatever):

    pure-authd -s /var/run/ftp.sock -r /usr/sbin/scalak-ftp-auth &
    pure-ftpd -l pam -l extauth:/var/run/ftp.sock -8 UTF-8 -u 0 -O clf:/var/log/pure-ftpd/transfer.log -E -B &

5) (Optional) Add /usr/sbin/scalak-remote-api to autostart, for 
   remote api support (via RabbitMQ).
