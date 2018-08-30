#!/bin/bash

set -x
set -e

 udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="Memberprinter" --set spoolHost="ucs-member.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
 udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshareMember" --set host="ucs-member.sambatest.local" --set path="/home/testshare"
 udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="Slaveprinter" --set spoolHost="ucs-slave.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
 udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshareSlave" --set host="ucs-slave.sambatest.local" --set path="/home/testshare"

