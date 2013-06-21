#!/bin/bash
# univention Join
# helper script: checks the join status of the local system

log_error () { # Log error message and exit
	local message="Error: $@"
	echo $message
}

check_join_status () {
	/usr/share/univention-join/check_join_status
}


