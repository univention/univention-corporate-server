#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import re

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Too many opened file descriptors by Samba')
description = _('Checks logfiles for "Too many open files" messages')


def run():
    stdout = ''
    stderr = ''
    success = True
    stdout += _('Checking samba logfiles for "Too many open files" messages\n')
    try:
    	with open('/var/log/samba/log.smbd', 'rb') as fd:
        	counter = re.findall('Too many open files', fd.read())
    except OSError:
    	pass  # logfile does not exists

    if counter:
        stderr += _('') #TODO: add description for solving the error
        success = False
    return success, stdout, stderr
