#!/usr/bin/python3
#
# Univention Management Console
#  Module lib containing low-lewel commands to control the UMC server
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
import time

from univention.lib.i18n import Translation
from univention.management.console.error import ServerError
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import SimpleThread, sanitize, simple_response
from univention.management.console.modules.sanitizers import StringSanitizer


_ = Translation('univention-management-console-module-lib').translate

CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']
CMD_ENABLE_EXEC_WITH_RESTART = '/usr/share/univention-updater/enable-apache2-umc'
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'


class Server:

    def restart_isNeeded(self, request):
        """
        TODO: It would be helpful to monitor the init.d scripts in order to
        determine which service exactly should be reloaded/restartet.
        """
        self.finished(request.id, True)

    def restart(self, request):
        """Restart apache, UMC Web server, and UMC server."""
        # send a response immediately as it won't be sent after the server restarts
        self.finished(request.id, True)

        # enable server restart and trigger restart
        # (disable first to make sure the services are restarted)
        subprocess.call(CMD_DISABLE_EXEC)
        p = subprocess.Popen(CMD_ENABLE_EXEC_WITH_RESTART, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _err = p.communicate()
        MODULE.info('enabling server restart: %s', out.decode('utf-8'))

    @simple_response
    def ping(self):
        return {"success": True}

    @sanitize(message=StringSanitizer(default=''))
    def reboot(self, request):
        message = _('The system will now be restarted')
        if request.options['message']:
            message = '%s (%s)' % (message, request.options['message'])

        if self._shutdown(message, reboot=True) != 0:
            raise ServerError(_('System could not reboot'))

        self.finished(request.id, None, message)

    @sanitize(message=StringSanitizer(default=''))
    def shutdown(self, request):
        message = _('The system will now be shut down')
        if request.options['message']:
            message = '%s (%s)' % (message, request.options['message'])

        if self._shutdown(message, reboot=False) != 0:
            raise ServerError(_('System could not shutdown'))

        self.finished(request.id, None, message)

    def _shutdown(self, message, reboot=False):
        action = '-r' if reboot else '-h'

        try:
            subprocess.call(('/usr/bin/logger', '-f', '/var/log/syslog', '-t', 'UMC', message))
        except (OSError, Exception):
            pass

        def halt():  # TODO: replace with timer instead of thread
            time.sleep(1.5)
            subprocess.call(('/sbin/shutdown', action, 'now', message))

        thread = SimpleThread('shutdown', halt, lambda t, r: None)
        thread.run()
        return 0
