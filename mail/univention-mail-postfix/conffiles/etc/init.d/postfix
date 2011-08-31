#!/bin/sh -e

# Start or stop Postfix
#
# LaMont Jones <lamont@debian.org>
# based on sendmail's init.d script

### BEGIN INIT INFO
# Provides:          postfix mail-transport-agent
# Required-Start:    $local_fs $remote_fs $syslog $named $network $time
# Required-Stop:     $local_fs $remote_fs $syslog $named $network
# Should-Start:      postgresql mysql clamav-daemon postgrey spamassassin
# Should-Stop:       postgresql mysql clamav-daemon postgrey spamassassin
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: start and stop the Postfix Mail Transport Agent
# Description:       postfix is a Mail Transport agent
### END INIT INFO

PATH=/bin:/usr/bin:/sbin:/usr/sbin
DAEMON=/usr/sbin/postfix
NAME=Postfix
TZ=
unset TZ

# Defaults - don't touch, edit /etc/default/postfix
SYNC_CHROOT="y"

test -f /etc/default/postfix && . /etc/default/postfix

test -x $DAEMON && test -f /etc/postfix/main.cf || exit 0

. /lib/lsb/init-functions
#DISTRO=$(lsb_release -is 2>/dev/null || echo Debian)

running() {
    queue=$(postconf -h queue_directory 2>/dev/null || echo /var/spool/postfix)
    if [ -f ${queue}/pid/master.pid ]; then
	pid=$(sed 's/ //g' ${queue}/pid/master.pid)
	# what directory does the executable live in.  stupid prelink systems.
	dir=$(ls -l /proc/$pid/exe 2>/dev/null | sed 's/.* -> //; s/\/[^\/]*$//')
	if [ "X$dir" = "X/usr/lib/postfix" ]; then
	    echo y
	fi
    fi
}

case "$1" in
    start)
	log_daemon_msg "Starting Postfix Mail Transport Agent" postfix
	RUNNING=$(running)
	if [ -n "$RUNNING" ]; then
	    log_end_msg 0
	else
	    # if you set myorigin to 'ubuntu.com' or 'debian.org', it's wrong, and annoys the admins of
	    # those domains.  See also sender_canonical_maps.

	    MYORIGIN=$(postconf -h myorigin | tr 'A-Z' 'a-z')
	    if [ "X${MYORIGIN#/}" != "X${MYORIGIN}" ]; then
		MYORIGIN=$(tr 'A-Z' 'a-z' < $MYORIGIN)
	    fi
	    if [ "X$MYORIGIN" = Xubuntu.com ] || [ "X$MYORIGIN" = Xdebian.org ]; then
		log_failure_msg "Invalid \$myorigin ($MYORIGIN), refusing to start"
		log_end_msg 1
		exit 1
	    fi

	    # see if anything is running chrooted.
	    NEED_CHROOT=$(awk '/^[0-9a-z]/ && ($5 ~ "[-yY]") { print "y"; exit}' /etc/postfix/master.cf)

	    if [ -n "$NEED_CHROOT" ] && [ -n "$SYNC_CHROOT" ]; then
		# Make sure that the chroot environment is set up correctly.
		oldumask=$(umask)
		umask 022
		cd $(postconf -h queue_directory)

		# if we're using tls, then we need to add etc/ssl/certs/ca-certificates.crt.
		if [ -f "/etc/ssl/certs/ca-certificates.crt" ]; then 
		    smtp_use_tls=$(postconf -h smtp_use_tls)
		    smtp_enforce_tls=$(postconf -h smtp_enforce_tls)
		    smtpd_use_tls=$(postconf -h smtpd_use_tls)
		    smtpd_enforce_tls=$(postconf -h smtpd_use_tls)
		    case :$smtp_use_tls:$smtp_enforce_tls:$smtpd_use_tls:$smtpd_enforce_tls: in
			*:yes:*)
			    mkdir -p etc/ssl/certs
			    cp /etc/ssl/certs/ca-certificates.crt etc/ssl/certs/
		    esac
		fi

		# if we're using unix:passwd.byname, then we need to add etc/passwd.
		local_maps=$(postconf -h local_recipient_maps)
		if [ "X$local_maps" != "X${local_maps#*unix:passwd.byname}" ]; then
		    if [ "X$local_maps" = "X${local_maps#*proxy:unix:passwd.byname}" ]; then
			sed 's/^\([^:]*\):[^:]*/\1:x/' /etc/passwd > etc/passwd
			chmod a+r etc/passwd
		    fi
		fi

		FILES="etc/localtime etc/services etc/resolv.conf etc/hosts \
		    etc/nsswitch.conf etc/nss_mdns.config"
		for file in $FILES; do 
		    [ -d ${file%/*} ] || mkdir -p ${file%/*}
		    if [ -f /${file} ]; then rm -f ${file} && cp /${file} ${file}; fi
		    if [ -f  ${file} ]; then chmod a+rX ${file}; fi
		done
		rm -f usr/lib/zoneinfo/localtime
		mkdir -p usr/lib/zoneinfo
		ln -sf /etc/localtime usr/lib/zoneinfo/localtime
		rm -f lib/libnss_*so*
		tar cf - /lib/libnss_*so* 2>/dev/null |tar xf -
		umask $oldumask
	    fi

	    if start-stop-daemon --start --exec ${DAEMON} -- quiet-quick-start; then
		log_end_msg 0
	    else
		log_end_msg 1
	    fi
	fi
    ;;

    stop)
	RUNNING=$(running)
	log_daemon_msg "Stopping Postfix Mail Transport Agent" postfix
	if [ -n "$RUNNING" ]; then
	    if ${DAEMON} quiet-stop; then
		log_end_msg 0
	    else
		log_end_msg 1
	    fi
	else
	    log_end_msg 0
	fi
    ;;

    restart)
        $0 stop
        $0 start
    ;;
    
    force-reload|reload)
	log_action_begin_msg "Reloading Postfix configuration"
	if ${DAEMON} quiet-reload; then
	    log_action_end_msg 0
	else
	    log_action_end_msg 1
	fi
    ;;

    status)
	RUNNING=$(running)
	if [ -n "$RUNNING" ]; then
	   log_success_msg "postfix is running"
	   exit 0
	else
	   log_success_msg "postfix is not running"
	   exit 3
	fi
    ;;

    flush|check|abort)
	${DAEMON} $1
    ;;

    *)
	log_action_msg "Usage: /etc/init.d/postfix {start|stop|restart|reload|flush|check|abort|force-reload}"
	exit 1
    ;;
esac

exit 0
