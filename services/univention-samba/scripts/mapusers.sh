#!/bin/bash

eval "$(ucr shell windows/domain)"
winbind_separator=$(testparm -sv -d0 --parameter-name="winbind separator" 2>/dev/null)
echo -nE "${1#$windows_domain$winbind_separator}"
