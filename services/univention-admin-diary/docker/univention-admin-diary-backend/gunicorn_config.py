# -*- coding: utf-8 -*-

#
# http://docs.gunicorn.org/en/19.6.0/settings.html
#

from multiprocessing import cpu_count

mode = 'wsgi'
working_dir = '/uadb'
user = 'root'
group = 'root'
bind = '0.0.0.0:8910'
workers = max(2, min(4, cpu_count()))
timeout = 30
reload = False
loglevel = 'debug'  # 'info'
capture_output = False
accesslog = '-'  # '/uadb/gunicorn_access.log'
errorlog = '-'  # ''/uadb/gunicorn_error.log'
syslog = False
proc_name = 'univention-admin-diary-backend'
