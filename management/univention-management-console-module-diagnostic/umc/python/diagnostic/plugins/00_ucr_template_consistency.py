#!/usr/bin/python2.7

import subprocess

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Consistency of UCR templates')
description = _('Verifys whether all installed UCR templates are in their original state')

def run():
	# FIXME
	return subprocess.call('/bin/bash', stdin='''
#!/bin/bash
output=$("univention-check-templates" 2>/dev/null)
if [ $? != 0 ]; then
	echo -e 'The following UCR templates have been modified, moved or are missing:\n'
	for line in $output; do
		echo $line
	done
	echo 'summary: Modified UCR templates found'
	exit 1
fi
echo "No modified UCR templates found"'''), '', ''
