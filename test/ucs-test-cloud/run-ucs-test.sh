#!/bin/sh
#
# Run ucs-test from init
#
set -x
HOME=/root
LOGNAME=root
USER=root
USERNAME=root
export HOME LOGNAME USER USERNAME
exec </dev/null >"$HOME/run.log" 2>&1 || true
cd "$HOME" || exit 1
# Clean up previous data
rm -rf "$HOME/ucs-test.log" "$HOME/test-reports"
# Run ucs-test
/usr/sbin/ucs-test -E dangerous -F junit -l "ucs-test.log"
# Send test-results via email
/root/smtp-send.py "ucs-test.log"
# Schedule shutdown in 1 minute
/sbin/shutdown -h -P 1
