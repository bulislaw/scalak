import os, sys
sys.path.append('/var/scalak/scalakweb')
os.environ['PYTHON_EGG_CACHE'] = '/var/scalak/python_egg_cache'

from paste.deploy import loadapp

application = loadapp('config:/var/scalak/scalakweb/production.ini')
