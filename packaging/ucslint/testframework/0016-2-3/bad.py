#!/usr/bin/python2.6
import subprocess
import univention_baseconfig
import univention_baseconfig as bc
from univention_baseconfig import *
import univention.config_registry
import univention.config_registry as ucr
from univention.config_registry import *

subprocess.call(('univention-baseconfig',))
subprocess.call(('/usr/sbin/univention-baseconfig', '-v'))
subprocess.call('univention-admin ')
subprocess.call(('/usr/sbin/univention-admin',))
subprocess.call(('/usr/share/univention-admin-tools/univention-dnsedit',))
subprocess.call(('/var/lib/univention-thinclient-root/usr/sbin/univention-admin',))
subprocess.call(('/var/lib/univention-thinclient-root/usr/sbin/univention-baseconfig',))
