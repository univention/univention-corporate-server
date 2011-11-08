<?php

@%@BCWARNING=// @%@

@!@

print "$this->applications['horde']['initial_page'] = '%s';" % baseConfig.get("horde/horde/initial_page", "imp")
print "$this->applications['ingo']['status']        = '%s';" % baseConfig.get("horde/ingo/status", "active")
print "$this->applications['horde']['status']       = '%s';" % baseConfig.get("horde/horde/status", "active")
print "$this->applications['imp']['status']         = '%s';" % baseConfig.get("horde/imp/status", "active")
print "$this->applications['kronolith']['status']   = '%s';" % baseConfig.get("horde/kronolith/status", "inactive")
print "$this->applications['mnemo']['status']       = '%s';" % baseConfig.get("horde/mnemo/status", "inactive")
print "$this->applications['nag']['status']         = '%s';" % baseConfig.get("horde/nag/status", "inactive")
print "$this->applications['turba']['status']       = '%s';" % baseConfig.get("horde/turba/status", "active")

@!@
