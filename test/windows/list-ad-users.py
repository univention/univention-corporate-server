import sys
import time

sys.path.append("lib")

import winexe

winexe = winexe.WinExe()
winexe.check_options()

winexe.winexec("ad-users")

sys.exit(0)

