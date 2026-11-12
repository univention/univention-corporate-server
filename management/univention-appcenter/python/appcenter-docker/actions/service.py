#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for starting/stopping an app
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import os.path
import subprocess

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.app_cache import Apps
from univention.appcenter.docker import MultiDocker
from univention.appcenter.ucr import ucr_get, ucr_is_false
from univention.appcenter.utils import call_process2


CONTAINER_SCRIPT = '/usr/lib/univention-appcenter/docker-app-container'
SYSTEMD_UNIT_DIR = '/etc/systemd/system'

SYSTEMD_UNIT = """\
# Created by the Univention App Center. Do not edit, it is overwritten when the app is registered.
# Use a drop-in in /etc/systemd/system/{unit}.d/ for local changes.
[Unit]
Description=Docker container of the UCS App Center app {app_id}
Wants=docker.service
After=docker.service remote-fs.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart={script} {app_id} start
ExecStop={script} {app_id} stop
ExecReload={script} {app_id} reload
TimeoutSec=5min

[Install]
WantedBy=multi-user.target
"""

INIT_WRAPPER = """\
#!/bin/sh
# Created by the Univention App Center. Do not edit, it is overwritten when the app is registered.
# The container of the app {app_id} is controlled by the systemd unit {unit}.
# This script is kept for compatibility and forwards to systemctl.
# The LSB header is needed by "systemctl enable", which also updates the SysV runlevel links.
### BEGIN INIT INFO
# Provides:          docker-app-{app_id}
# Required-Start:    $remote_fs $syslog docker
# Required-Stop:     $remote_fs $syslog docker
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Docker container of the UCS App Center app {app_id}
### END INIT INFO
case "$1" in
    start|stop|restart|reload) exec systemctl "$1" {unit} ;;
    crestart) exec systemctl try-restart {unit} ;;
    kill|status) exec {script} {app_id} "$1" ;;
    *) echo "Usage: $0 {{start|stop|restart|reload|crestart|kill|status}}" >&2; exit 1 ;;
esac
"""


def get_unit_name(app_id):
    return 'docker-app-%s.service' % app_id


def get_unit_path(app_id):
    return os.path.join(SYSTEMD_UNIT_DIR, get_unit_name(app_id))


def get_init_path(app_id):
    return '/etc/init.d/docker-app-%s' % app_id


def install_systemd_unit(app_id):
    """
    Write the systemd unit and the /etc/init.d compatibility wrapper of the app container,
    and enable or disable the unit according to <app_id>/autostart.
    """
    fmt = {'app_id': app_id, 'unit': get_unit_name(app_id), 'script': CONTAINER_SCRIPT}
    init_script = get_init_path(app_id)
    with open(get_unit_path(app_id), 'w') as fd:
        fd.write(SYSTEMD_UNIT.format(**fmt))
    with open(init_script, 'w') as fd:
        fd.write(INIT_WRAPPER.format(**fmt))
    os.chmod(init_script, 0o755)
    subprocess.call(['/bin/systemctl', 'daemon-reload'])
    set_systemd_unit_autostart(app_id)


def set_systemd_unit_autostart(app_id):
    """Enable the unit for autostart=yes (or unset), disable it for autostart=manually or no."""
    key = '%s/autostart' % app_id
    if ucr_is_false(key) or (ucr_get(key) or '').lower() == 'manually':
        action = 'disable'
    else:
        action = 'enable'
    subprocess.call(['/bin/systemctl', action, '--quiet', get_unit_name(app_id)])


def remove_systemd_unit(app_id):
    unit = get_unit_name(app_id)
    # the container is removed separately; stopping only makes systemd forget the unit
    subprocess.call(['/bin/systemctl', 'stop', unit])
    subprocess.call(['/bin/systemctl', 'disable', '--quiet', unit])
    for path in (get_unit_path(app_id), get_init_path(app_id)):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    subprocess.call(['/usr/sbin/update-rc.d', '-f', os.path.basename(get_init_path(app_id)), 'remove'], stdout=subprocess.DEVNULL)
    subprocess.call(['/bin/systemctl', 'daemon-reload'])
    subprocess.call(['/bin/systemctl', 'reset-failed', unit], stderr=subprocess.DEVNULL)


class Service(UniventionAppAction):

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be controlled')

    @classmethod
    def get_init(cls, app):
        return get_unit_path(app.id)

    def call_init(self, app, command):
        if not os.path.exists(self.get_init(app)):
            self.fatal('%s is not supported' % app.id)
            return False
        if command in ('start', 'stop', 'restart', 'reload', 'crestart'):
            # through systemd, so that it knows whether the container has to be stopped on shutdown
            verb = 'try-restart' if command == 'crestart' else command
            return self._call_script('/bin/systemctl', verb, get_unit_name(app.id))
        return self._call_script(CONTAINER_SCRIPT, app.id, command)


class Start(Service):
    """Starts an application previously installed."""

    help = 'Start an app'

    def main(self, args):
        if args.app.uses_docker_compose():
            docker = MultiDocker(args.app)
            return docker.start()
        return self.call_init(args.app, 'start')


class Stop(Service):
    """Stops a running application."""

    help = 'Stop an app'

    def main(self, args):
        if args.app.uses_docker_compose():
            docker = MultiDocker(args.app)
            return docker.stop()
        return self.call_init(args.app, 'stop')


class Restart(Service):
    """Restarts an app. Stops and Starts. Does not have to be running"""

    help = 'Restart an app'

    def main(self, args):
        if args.app.uses_docker_compose():
            docker = MultiDocker(args.app)
            return docker.restart()
        return self.call_init(args.app, 'restart')


class CRestart(Service):
    """CRestarts an app. Stops and Starts. Has to be running"""

    help = 'CRestart an app'

    def main(self, args):
        if args.app.uses_docker_compose():
            docker = MultiDocker(args.app)
            return docker.restart()
        return self.call_init(args.app, 'crestart')


class Status(Service):
    """Ask service about status. Possible answers: running stopped"""

    help = 'Retrieve status of an app'

    @classmethod
    def _container_app(cls, app):
        if app.plugin_of:
            return Apps().find(app.plugin_of)
        return app

    def main(self, args):
        if args.app.uses_docker_compose():
            docker = MultiDocker(args.app)
            running = docker.is_running()
            if running:
                self.log('App is running')
            else:
                self.log('App is not running')
            return running
        return self.call_init(self._container_app(args.app), 'status')

    @classmethod
    def get_status(cls, app):
        if app.uses_docker_compose():
            return ''
        else:
            try:
                _ret, out = call_process2([CONTAINER_SCRIPT, cls._container_app(app).id, 'status'])
                # dirty, but we have a limit for sending status information
                out = out[500:]
            except Exception as e:
                out = str(e)
            return out
