#!/usr/bin/python2.6
import subprocess
import univention_baseconfig  # noqa: F401
import univention_baseconfig as bc  # noqa: F401
from univention_baseconfig import *  # noqa: F403,F401
import univention.config_registry  # noqa: F401
import univention.config_registry as ucr  # noqa: F401
from univention.config_registry import *  # noqa: F403,F401

subprocess.call(('univention-baseconfig',))
subprocess.call(('/usr/sbin/univention-baseconfig', '-v'))
subprocess.call('univention-admin ')
subprocess.call(('/usr/sbin/univention-admin',))
subprocess.call(('/usr/share/univention-admin-tools/univention-dnsedit',))
subprocess.call(('/var/lib/univention-thinclient-root/usr/sbin/univention-admin',))
subprocess.call(('/var/lib/univention-thinclient-root/usr/sbin/univention-baseconfig',))
