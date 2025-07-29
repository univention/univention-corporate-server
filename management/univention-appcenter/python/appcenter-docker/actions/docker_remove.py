#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for uninstalling an app
#  (docker version)
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.remove import Remove
from univention.appcenter.actions.service import Stop
from univention.appcenter.exceptions import RemoveBackupFailed, RemovePluginUnsupported


class Remove(Remove, DockerActionMixin):

    def setup_parser(self, parser):
        super().setup_parser(parser)
        parser.add_argument('--do-not-backup', action='store_false', dest='backup', help='For docker apps, do not save a backup container')

    def _do_it(self, app, args):
        self._unregister_host(app, args)
        self.percentage = 5
        super()._do_it(app, args)

    def _remove_app(self, app, args):
        if not app.docker:
            return super()._remove_app(app, args)
        else:
            if app.plugin_of:
                raise RemovePluginUnsupported()
            else:
                return self._remove_docker_container(app, args)

    def _remove_docker_container(self, app, args):
        self._configure(app, args)
        if args.backup and self._backup_container(app, remove=True) is False:
            raise RemoveBackupFailed()
        docker = self._get_docker(app)
        Stop.call(app=app)
        docker.stop()
        docker.rm()
        return True

    def dry_run(self, app, args):
        if not app.docker:
            return super().dry_run(app, args)
        self.log('%s is a Docker App. No sane dry run is implemented' % app)
