#!/bin/sh
# Univention Net Installer Daemon
#  init script
#
# Copyright 2010-2019 Univention GmbH
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
#
### BEGIN INIT INFO
# Provides:          univention-net-installer-daemon
# Required-Start:    $network $local_fs
# Required-Stop:
# Should-Start:      $named slapd
# Should-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Univention Net Installer Daemon
# Description:       Service to reset the reinstall flag
### END INIT INFO
# pidfile: /var/run/univention-net-installer-daemon.pid

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

DAEMON=/usr/sbin/univention-net-installer-daemon  # Introduce the server's location here
NAME="univention-net-installer-daemon"              # Introduce the short server's name here
DESC="Univention Net Installer Daemon" # Introduce a short description here
LOGDIR=/var/log/univention # Log directory to use

PIDFILE=/var/run/$NAME.pid

test -x "$DAEMON" || exit 0

. /lib/lsb/init-functions

# Default options, these can be overridden by the information
# at /etc/default/$NAME
DAEMON_OPTS="-p 49173 -D -d 1"        # Additional options given to the server

DIETIME=10              # Time to wait for the server to die, in seconds
                        # If this value is set too low you might not
                        # let some servers to die gracefully and
                        # 'restart' will not work

STARTTIME=2            # Time to wait for the server to start, in seconds
                        # If this value is set each time the server is
                        # started (on start or restart) the script will
                        # stall to try to determine if it is running
                        # If it is not set and the server takes time
                        # to setup a pid file the log message might 
                        # be a false positive (says it did not start
                        # when it actually did)
                        
LOGFILE="$LOGDIR/$NAME.log"  # Server logfile

# Include defaults if available
if [ -f "/etc/default/$NAME" ] ; then
	. "/etc/default/$NAME"
fi

set -e

running_pid() {
# Check if a given process pid's cmdline matches a given name
    pid=$1
    name=$2
    [ -z "$pid" ] && return 1
    [ ! -d /proc/$pid ] &&  return 1
    cmd=`cat /proc/$pid/cmdline | tr "\000" "\n"|sed -ne 2p |cut -d : -f 1`
    # Is this the expected server
    [ "$cmd" != "$name" ] &&  return 1
    return 0
}

running() {
# Check if the process is running looking at /proc
    # No pidfile, probably no daemon present
    [ ! -f "$PIDFILE" ] && return 1
    pid=`cat $PIDFILE`
    running_pid $pid "$DAEMON" || return 1
    return 0
}

start_server() {
	start_daemon -p "$PIDFILE" "$DAEMON" $DAEMON_OPTS
	errcode=$?
	return $errcode
}

stop_server() {
	killproc -p "$PIDFILE" "$DAEMON"
	errcode=$?
	return $errcode
}

reload_server() {
    [ ! -f "$PIDFILE" ] && return 1
    pid=pidofproc $PIDFILE # This is the daemon's pid
    # Send a SIGHUP
    kill -1 $pid
    return $?
}

force_stop() {
# Force the process to die killing it manually
	[ ! -e "$PIDFILE" ] && return
	if running ; then
		kill -15 $pid
	# Is it really dead?
		sleep "$DIETIME"s
		if running ; then
			kill -9 $pid
			sleep "$DIETIME"s
			if running ; then
				echo "Cannot kill $NAME (pid=$pid)!"
				exit 1
			fi
		fi
	fi
	rm -f "$PIDFILE"
}


case "$1" in
  start)
	log_daemon_msg "Starting $DESC " "$NAME"
        # Check if it's running first
        if running ;  then
            log_progress_msg "apparently already running"
            log_end_msg 0
            exit 0
        fi
        if start_server ; then
            # NOTE: Some servers might die some time after they start,
            # this code will detect this issue if STARTTIME is set
            # to a reasonable value
            [ -n "$STARTTIME" ] && sleep $STARTTIME # Wait some time 
            if  running ;  then
                # It's ok, the server started and is running
                log_end_msg 0
            else
                # It is not running after we did start
                log_end_msg 1
            fi
        else
            # Either we could not start it
            log_end_msg 1
        fi
	;;
  stop)
        log_daemon_msg "Stopping $DESC" "$NAME"
        if running ; then
            # Only stop the server if we see it running
			errcode=0
            stop_server || errcode=$?
            log_end_msg $errcode
        else
            # If it's not running don't do anything
            log_progress_msg "apparently not running"
            log_end_msg 0
            exit 0
        fi
        ;;
  force-stop)
        # First try to stop gracefully the program
        "$0" stop
        if running; then
            # If it's still running try to kill it more forcefully
            log_daemon_msg "Stopping (force) $DESC" "$NAME"
			errcode=0
            force_stop || errcode=$?
            log_end_msg $errcode
        fi
	;;
  restart|force-reload)
        log_daemon_msg "Restarting $DESC" "$NAME"
		errcode=0
        stop_server || errcode=$?
        # Wait some sensible amount, some server need this
        [ -n "$DIETIME" ] && sleep $DIETIME
        start_server || errcode=$?
        [ -n "$STARTTIME" ] && sleep $STARTTIME
        running || errcode=$?
        log_end_msg $errcode
	;;
  status)

        log_daemon_msg "Checking status of $DESC" "$NAME"
        if running ;  then
            log_progress_msg "running"
            log_end_msg 0
        else
            log_progress_msg "apparently not running"
            log_end_msg 1
            exit 1
        fi
        ;;
  # Use this if the daemon cannot reload
  reload)
        log_warning_msg "Reloading $NAME daemon: not implemented, as the daemon"
        log_warning_msg "cannot re-read the config file (use restart)."
        ;;
  *)
	echo "Usage: $0 {start|stop|force-stop|restart|force-reload|status}" >&2
	exit 1
	;;
esac

exit 0
# vim:set ft=sh:
