import sys
import time

sys.path.append("lib")

import winexe

winexe = winexe.WinExe()
winexe.check_options()

if len(winexe.args) < 1:
	winexe.error_and_exit("need a command to execute")

command = winexe.args[0]
args = winexe.args[1:]

winexe.winexec(command, " ".join(args))

sys.exit(0)

