#!/usr/bin/python
import debug as ud

fd = ud.init("stdout", ud.NO_FLUSH, ud.FUNCTION)
assert isinstance(fd, file)

ud.debug(ud.MAIN, ud.ERROR, "Error in main: %%%")
ud.debug(ud.MAIN, ud.WARN, "Warning in main: %%%")
ud.debug(ud.MAIN, ud.PROCESS, "Process in main: %%%")
ud.debug(ud.MAIN, ud.INFO, "Information in main: %%%")
ud.debug(ud.MAIN, ud.ALL, "All in main: %%%")

ud.set_level(ud.MAIN, ud.PROCESS)
l = ud.get_level(ud.MAIN)
assert l == ud.PROCESS

ud.reopen()

ud.set_function(ud.FUNCTION)
ud.begin("Function")
ud.end("Function")

ud.set_function(ud.NO_FUNCTION)
ud.begin("No function")
ud.end("No function")

ud.exit()

ud.set_level(ud.MAIN, ud.ALL)
l = ud.get_level(ud.MAIN)
assert l != ud.ALL

ud.debug(ud.MAIN, ud.ALL, "No crash")
