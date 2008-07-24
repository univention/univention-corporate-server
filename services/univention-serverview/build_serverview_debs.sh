#!/bin/sh

# http://download.fujitsu-siemens.com/prim_supportcd/html/SNMP_Agents_e.html

SERVER_URL="http://download.fujitsu-siemens.com/prim_supportcd/Software/ServerView/Linux/Agents/"
AGENTS="srvmagt-mods_src srvmagt-eecd srvmagt-agents srvmagt-scs"
VERSION="4.60-08"
EXTENSION=".suse.rpm"

if [ "$(whoami)" != root ]; then
	echo "ERROR: Please run as root"
	exit 1
fi

for a in $AGENTS; do
	if [ ! -e "${a}-${VERSION}${EXTENSION}" ]; then
		wget "${SERVER_URL}/${a}-${VERSION}${EXTENSION}"
	fi
done

for a in $AGENTS; do
	alien ${a}-${VERSION}${EXTENSION}
done

exit 0
