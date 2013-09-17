#!/bin/bash
#
# Copyright 2013 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#

TARGETDIR="$(dirname "$0")"
if [ "$TARGETDIR" = "." ] ; then
	TARGETDIR="$(pwd)"
fi
LOG="$TARGETDIR/$(basename "$0" .sh).log"

if [ -z "$1" -o "$1" = "-h" -o "$1" = "--help" ] ; then
	echo "Syntax: $(basename "$0") [--help] <SVN-URI>"
	echo
	echo "This script fetches the given version of shim from SVN"
	echo "and creates a new binary build."
	echo
	echo "Example: $(basename "$0") svn+ssh://USER@billy:/var/svn/dev/branches/ucs-3.2/ucs-3.2-0/base/shim"
	exit 1
fi

fail () {
	echo "fail"
	echo "ERROR: $1" >&2
	exit 1
}

. /usr/share/univention-lib/all.sh


date >> "$LOG"

echo -n "Check architecture: "
[ "$(uname -m)" = "x86_64" ] && echo "ok" || fail "wrong architecture"

echo -n "Check UCS version: "
eval "$(ucr shell version/version)"
[ "$version_version" = "3.2" -o "$version_version" = "3.3" ] && echo "ok" || fail "at least UCS version 3.2 is required"

echo -n "Check custom sources.list: "
FN="/etc/apt/sources.list.d/univention-secure-boot.list"
ENTRY="deb http://192.168.0.10/build2/ ucs_${version_version}-0-uefi"
if [ ! -f "$FN" ] ; then
 	echo "$ENTRY/all/" >> "$FN"
 	echo "$ENTRY/\$(ARCH)/" >> "$FN"
 	echo "Created $FN" >> "$LOG"
 	echo "updated"
else
 	echo "ok"
fi

echo -n "Check update/secure_apt: "
if is_ucr_true update/secure_apt ; then
	ucr set update/secure_apt=no >> "$LOG"
	echo "updated"
else
	echo "ok"
fi

echo -n "Check repository/online/unmaintained: "
if ! is_ucr_true repository/online/unmaintained ; then
	ucr set repository/online/unmaintained=yes >> "$LOG"
	echo "updated"
else
	echo "ok"
fi

echo -n "Check build environment: "
univention-install -y --force-yes subversion build-essential sbsigntool gnu-efi debhelper libnss3-tools >> "$LOG" 2>> "$LOG" && echo "ok" || fail "Package installation failed. Please check $LOG"

###TMPDIR="$(mktemp -d $(pwd)/shim.XXXXXXX)"  # FIXME
TMPDIR=/root/src && cd /root/src # FIXME

echo "Build directory: $TMPDIR"
echo "Build directory: $TMPDIR" >> "$LOG"

echo "Fetching source of shim:"
cd "$TMPDIR"
svn co "$1" >> "$LOG" 2>> "$LOG"
cd shim && echo "Fetching source of shim: ok" || fail "Failed to fetch shim from SVN. Please check $LOG"

echo -n "Building shim: "
debian/rules clean binary 2>> "$LOG" >> "$LOG" && echo "ok" || fail "Check $LOG"

echo "NOTE: shim.efi has to be signed by Microsoft"
