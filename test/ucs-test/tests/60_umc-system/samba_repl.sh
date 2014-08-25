. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/samba.sh" || exit 137

username="$1"

if checkpkg "univention-samba4" 2>/dev/null; then
	wait_for_drs_replication "(sAMAccountName=$username)" objectSid
else
        echo 'No need to wait for replication in S3 environment...'
fi

exit $RETVAL
