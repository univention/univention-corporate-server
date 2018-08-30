#!/bin/bash

set -x
set -e

 python shared-utils/ucs-winrm.py check-share --server $MEMBER --sharename "testshareMember" --driveletter R --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
 python shared-utils/ucs-winrm.py check-share --server $SLAVE --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
 #python shared-utils/ucs-winrm.py setup-printer --printername Slaveprinter --server "$SLAVE"
 #python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER"
 python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$SLAVE\Slaveprinter" --impersonate --run-as-user Administrator
 python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$MEMBER\Memberprinter" --impersonate --run-as-user Administrator
 sleep 20
 python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER --impersonate --run-as-user Administrator 
 python shared-utils/ucs-winrm.py print-on-printer --printername Slaveprinter --server $SLAVE --impersonate --run-as-user Administrator
 samba-tool ntacl sysvolreset || true
