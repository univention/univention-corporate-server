import sys
import time

sys.path.append("lib")

import winexe

winexe = winexe.WinExe()
winexe.options.add_option("--dns-server", dest="dns_server", help="the dns server for the domain")
winexe.check_options()

winexe.winexec("set-dns-server", winexe.opts.dns_server, domain=False)
winexe.winexec("domain-join", winexe.opts.domain, winexe.opts.domain_admin, winexe.opts.domain_password, domain=False)
winexe.winexec("firewall-turn-off")

winexe.winexec("reboot")
winexe.wait_until_client_is_gone(timeout=60)
winexe.wait_for_client(timeout=60)

winexe.winexec("check-domain", winexe.opts.domain)
winexe.winexec("activate-ts-service")

sys.exit(0)

