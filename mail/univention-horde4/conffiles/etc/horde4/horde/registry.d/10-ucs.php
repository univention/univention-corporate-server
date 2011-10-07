<?php

@%@BCWARNING=// @%@

@!@

# print variable if set
def setVar(phpName, ucrName):
    if baseConfig.get(ucrName):
        print phpName + " = %s;" % baseConfig[ucrName]

setVar("$this->applications['horde']['initial_page']", "horde/horde/initial_page")
setVar("$this->applications['ingo']['status']", "horde/ingo/status")
setVar("$this->applications['horde']['status']", "horde/horde/status")
setVar("$this->applications['imp']['status']", "horde/imp/status")
setVar("$this->applications['kronolith']['status']", "horde/kronolith/status")
setVar("$this->applications['mnemo']['status']", "horde/mnemo/status")
setVar("$this->applications['nag']['status']", "horde/nag/status")
setVar("$this->applications['turba']['status']", "horde/turba/status")

@!@
