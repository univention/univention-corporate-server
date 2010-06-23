#!/bin/sh
#
# Univention Client Basesystem
#  helper script for building the kernel for the client basesystem
#
# Copyright 2001-2010 Univention GmbH
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

archive="$1"
tmpdir="/tmp/$$"

if ! test -f "$1"; then
    echo "Package 'archive' does not exist."
    exit 1
fi

test -e "$tmpdir" && exit 1
mkdir -m 700 "$tmpdir"

basename=`basename $archive`
package=${basename/_*}
suffix=${basename#$package}
npackage="univention-client-$package"

mkdir -p "$tmpdir/var/lib/univention-client-root"
mkdir "$tmpdir/DEBIAN"

dpkg-deb -x $archive $tmpdir
dpkg-deb -e $archive "$tmpdir/DEBIAN"

cd $tmpdir

mv "usr/share/doc/$package" "usr/share/doc/$npackage"

if echo $package | grep -q '^kernel-image-'; then

    mv boot var/lib/univention-client-boot
    mv lib var/lib/univention-client-root/
    ln -s `basename var/lib/univention-client-boot/vmlinuz*` var/lib/univention-client-boot/linux
    for i in var/lib/univention-client-root/lib/modules/*/modules.*; do
	ln -fs /ramdisk/`basename $i` $i
    done

    rm -f DEBIAN/postinst DEBIAN/postrm DEBIAN/preinst DEBIAN/prerm
#    sed 's/^Provides: .*/Provides: univention-client-kernel-image/;
#         s/^Package: \(.*\)/Package: univention-client-\1/' \
    grep -v "^Provides: " DEBIAN/control \
    | sed "s/^Package: \(.*\)/Package: univention-client-\1/" \
	> DEBIAN/control.new
    mv DEBIAN/control.new DEBIAN/control

else

    mv lib var/lib/univention-client-root/

    rm -f DEBIAN/postinst DEBIAN/postrm DEBIAN/preinst DEBIAN/prerm
    sed 's/^Package: \(.*\)/Package: univention-client-\1/;
         s/^Depends: \(.*\)/Depends: univention-client-\1/' \
	< DEBIAN/control > DEBIAN/control.new
    mv DEBIAN/control.new DEBIAN/control

fi

cd -
dpkg-deb -b "$tmpdir" "$npackage$suffix"
rm -rf "$tmpdir"
