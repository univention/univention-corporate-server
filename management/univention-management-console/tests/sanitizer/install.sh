#!/usr/bin/bash

install -d /usr/share/pyshared/univention/management/console/modules/sanitize/

install -m755 __init__.py /usr/share/pyshared/univention/management/console/modules/sanitize/__init__.py
install -m644 sanitize.xml /usr/share/univention-management-console/modules/

. /usr/share/univention-lib/umc.sh
umc_operation_create "sanitize-all" "sanitizer" "" "sanitize/*"
umc_policy_append "default-umc-all" "sanitize-all"
