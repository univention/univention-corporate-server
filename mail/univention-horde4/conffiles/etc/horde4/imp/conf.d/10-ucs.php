<?php

@%@BCWARNING=// @%@

@!@

# print variable if set
def setVar(phpName, ucrName):
	if baseConfig.get(ucrName):
		print phpName + " = %s;" % baseConfig[ucrName]

setVar("$conf['menu']['apps_iframe']", "horde/imp/menu/apps_iframe")
setVar("$conf['menu']['apps']", "horde/menu/apps")

@!@

