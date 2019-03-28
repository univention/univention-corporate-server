#!/bin/bash

set -x
set -e

run_umc_tests () {
	. utils.sh
	run_tests -r umc-producttest
	run_tests -s checks -s base -s udm -s umc -s selenium -s udm-users -s udm-groups -s udm-containers -s udm-printers -s udm-dhcp -s udm-computers -s udm-dns -s udm-extendedattribute -s udm-syntax -s udm-net -s udm-settings -s udm-extensions
}

run_umc_join () {
	/usr/share/ucs-test/86_selenium/110_product_test_do_rejoin -f
	univention-check-join-status
}

umc_reboot_server() {
	/usr/share/ucs-test/86_selenium/138_reboot_server -f
}

check_uptime() {
	[ "$(uptime  -p | sed 's/^up //g; s/ minutes$//g')" -lt 7 ]
}
