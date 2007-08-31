#! /bin/sh

case "$1" in
  start)
	echo -n "Starting univention-fax-server: "
	faxmodem faxCAP
	echo "faxCAPI"
	;;
  stop)
	true
	;;
  *)
	echo "Usage: $0 {start|stop}" >&2
	exit 1
	;;
esac

exit 0

