#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

: "${SSH_KEY:=$HOME/ec2/keys/tech.pem}"

fetch-files () { # [<USER>@]<IP-ADDRESS> <REMOTE-FILE(S)> <DESTINATION> [SCP-ARGS...]
	local ADDR="${1#*@}"
	local USER="${1%$ADDR}"
	local FILES="$2"
	local TARGET="$3"
	shift 3
	[ $# -eq 0 ] && set -- -i "$SSH_KEY" -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no

	case "$ADDR" in [![]*:*:*[!]]) ADDR="[$ADDR]" ;; esac

	set -- scp "$@" "${USER:-root@}${ADDR}:${FILES}" "$TARGET"
	echo "$*"
	"$@"
}

fetch-results () { # <IP-ADDRESS> [TARGET-DIR]
	# check env
	if [ "${UCS_TEST_RUN:-}" = "false" ]; then
		echo "ucs-test disabled by env UCS_TEST_RUN=$UCS_TEST_RUN, so no results i guess"
		return 0
	fi

	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR/selenium"
	mkdir -p "$TARGETDIR/tracebacks"
	# shellcheck disable=SC2191
	declare -a FILES=(
		'artifacts'
		'packages-under-test.log'
		'test-reports'
		'ucs-test.log'
		'/usr/share/ucs-test/*/selenium'
		'/var/log/apache2/error.log'='apache2-error.log'
		'/var/log/apache2/access.log'='apache2-access.log'
		'/var/log/auth.log*'=
		'/var/log/apt/term.log'
		'/var/log/daemon.log*'=
		'/var/log/dpkg.log'
		'/var/log/kern.log'
		'/var/log/dovecot.log*'=
		'/var/log/journalctl.log'
		'/var/log/mail.log*'=
		'/var/log/samba/*'=
		'/var/log/univention/sysvol-sync.log'
		'/var/log/syslog*'=
		'/var/log/univention/actualise.log'
		'/var/log/univention/appcenter.log'
		'/var/log/univention/portal.log'
		'/var/log/univention/config-registry.replog'='config-registry.replog.log'
		'/var/log/univention/connector*'=
		'/var/log/univention/coverage'
		'/var/log/univention/directory-manager-cmd.log*'=
		'/var/log/univention/directory-manager-rest.log'
		'/var/log/univention/join.log'
		'/var/log/univention/listener.log'
		'/var/log/univention/listener_modules/*.log'
		'/var/log/univention/management*'=
		'/var/log/univention/notifier.log'
		'/var/log/univention/setup.log'
		'/var/log/univention/system-stats.log'
		'/var/log/univention/ucs-windows-tools.log'
		'/var/log/univention/ucs-school-import'
		'/var/log/univention/ucs-school-import.*'=
		'/var/log/univention/ucs-school-import-*'=
		'/var/log/univention/ucsschool-apis'
		'/var/log/univention/ucsschool-id-connector'
		'/var/log/univention/ucsschool-kelvin-rest-api'
		'/var/log/univention/reload-service.log'
		'/var/log/univention/updater.log'
		'/var/log/univention/server_password_change.log'
		'/var/log/univention/37check-ucr-templates-py3-migration-status.md'
		'/var/lib/univention-directory-replication/failed.ldif'
	)
	local FILE rc=0
	for FILE in "${FILES[@]}"; do
		fetch-files "root@${ADDR}" "${FILE%=*}" "${TARGETDIR}/${FILE##*[/=]}" || rc=$?
	done
	cp "${TARGETDIR}/test-reports/99_end/01_var_log_tracebacks.py.xml" "${TARGETDIR}/tracebacks/" || true
	return $rc
}

fetch-coverage () {
	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR"
	fetch-files "root@${ADDR}" "htmlcov/" "$TARGETDIR"
}

# === MAIN ===

ACTION="$1"
shift || exit 1

case "$ACTION" in
	fetch-files)
		fetch-files "$@"
		;;
	fetch-results|ucsschool-fetch-results)
		fetch-results "$@" || :
		;;
	fetch-coverage)
		fetch-coverage "$@"
		;;
	*)
		echo "Unknown action: $ACTION"
		;;
esac

# vim:set filetype=sh ts=4:
