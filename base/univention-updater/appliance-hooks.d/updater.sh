#!/bin/sh

# Re-create the system uuid
ucr set uuid/system="$(cat /proc/sys/kernel/random/uuid)"

# Identify this system as appliance
if [ -z "$(ucr get updater/identify)" ]; then
	ucr set updater/identify="UCS (appliance)"
fi

exit 0

