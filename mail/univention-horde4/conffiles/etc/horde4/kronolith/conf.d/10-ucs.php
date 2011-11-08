<?php

@%@BCWARNING=// @%@

@!@

apps = baseConfig.get("horde/kronolith/menu/apps", "imp,ingo,turba")
apps = "', '".join(apps.split(","))
apps = "'" + apps + "'"

print "$conf['menu']['apps'] = array(%s);" % apps
print "$conf['menu']['apps_iframe'] = %s;" % baseConfig.get("horde/kronolith/menu/apps_iframe", "true")

@!@

?>
