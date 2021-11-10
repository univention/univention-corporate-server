#!/bin/bash

testparm_output=$(testparm -sv -d0 2>/dev/null)
windows_domain=$(sed -n 's/^\tworkgroup = //p' <<<"$testparm_output")
winbind_separator=$(sed -n 's/^\twinbind separator = //p' <<<"$testparm_output")
echo -nE "${1#$windows_domain$winbind_separator}"
