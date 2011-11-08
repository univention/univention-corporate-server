<?php

@%@BCWARNING=// @%@

@!@

apps = baseConfig.get("horde/imp/menu/apps", "imp,ingo,turba")
apps = "', '".join(apps.split(","))
apps = "'" + apps + "'"

print "$conf['menu']['apps'] = array(%s);" % apps
print "$conf['menu']['apps_iframe'] = %s;" % baseConfig.get("horde/imp/menu/apps_iframe", "true")

@!@

