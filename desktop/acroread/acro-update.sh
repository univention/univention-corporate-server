#!/bin/bash
#
# Copyright 2004-2012 Univention GmbH
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

release_scope_name="$1"
ACROREAD_RELEASE="$2"
METHOD=http

[ -n "$release_scope_name" ] || { echo "usage: $0 <release-scope> [<Acroread-Version>]"; exit 1; }

externaptdir="/var/univention/buildsystem2/apt/${release_scope_name}/extern"
[ -d "$externaptdir" ] || { echo "$externaptdir does not exists, check release-scope"; exit 1; }

if [ -z "$ACROREAD_RELEASE" ]; then # run uscan to find the latest release

ACROREAD_RELEASE="$(cat <<%WATCHFILE | uscan --report --watchfile - | sed -n 's/.*Newer version (\(.*\)) available on remote site:/\1/p'
# format version number, currently 3; this line is compulsory!
version=3

opts=pasv ftp://ftp.adobe.com/pub/adobe/reader/unix/(\\d).x/(\\d\.[\\.\\d]*)/deu/AdbeRdr([\\d\\.]+)-1_i386linux_deu\\.deb debian
%WATCHFILE
)"

fi

[ -n "$ACROREAD_RELEASE" ] || { echo "usage: $0 <release-scope> [<Acroread-Version>]"; exit 1; }

ACROREAD_MAJOR="${ACROREAD_RELEASE/.*}"

case "${METHOD}" in
	ftp) baseurl="ftp://ftp.adobe.com/pub/adobe/reader/unix/${ACROREAD_MAJOR}.x/${ACROREAD_RELEASE}/"; break;;
	http) baseurl="http://ardownload.adobe.com/pub/adobe/reader/unix/${ACROREAD_MAJOR}.x/${ACROREAD_RELEASE}/"; break;;
esac

case "${ACROREAD_MAJOR}" in
	8) upstream_debfile_enu=AdobeReader_enu-${ACROREAD_RELEASE}-1.i386.deb;
	   upstream_debfile_deu=AdobeReader_deu-${ACROREAD_RELEASE}-1.i386.deb;
	   break;;
	9) upstream_debfile_enu=AdbeRdr${ACROREAD_RELEASE}-1_i386linux_enu.deb;
	   upstream_debfile_deu=AdbeRdr${ACROREAD_RELEASE}-1_i386linux_deu.deb;
	   break;;
	*) echo "Major release not supported yet"; exit 1; break;;
esac

wget ${baseurl}deu/${upstream_debfile_deu} ${baseurl}enu/${upstream_debfile_enu}

echo "Need to sudo to chown package contents for root: "
sudo -s -H
mkdir -p adobereader-deu/DEBIAN; chmod 755 adobereader-deu/DEBIAN
dpkg -x ${upstream_debfile_deu} adobereader-deu
dpkg -e ${upstream_debfile_deu} adobereader-deu/DEBIAN
chmod u+w adobereader-deu/DEBIAN/control
chown -R 0.0 adobereader-deu
echo "Conflicts: acroread-de (<< ${ACROREAD_RELEASE}), adobereader-enu" >> adobereader-deu/DEBIAN/control
dpkg-deb -b adobereader-deu . && mv adobereader-deu_${ACROREAD_RELEASE}_i386.deb AdobeReader-deu_${ACROREAD_RELEASE}-1_i386.deb
sed -i 's/^Architecture: i386/Architecture: amd64/' adobereader-deu/DEBIAN/control
dpkg-deb -b adobereader-deu . && mv adobereader-deu_${ACROREAD_RELEASE}_amd64.deb AdobeReader-deu_${ACROREAD_RELEASE}-1_amd64.deb
rm -rf adobereader-deu ${upstream_debfile_deu}

mkdir -p adobereader-enu/DEBIAN; chmod 755 adobereader-enu/DEBIAN
dpkg -x ${upstream_debfile_enu} adobereader-enu
dpkg -e ${upstream_debfile_enu} adobereader-enu/DEBIAN
chmod u+w adobereader-enu/DEBIAN/control
chown -R 0.0 adobereader-enu
echo "Conflicts: acroread (<< ${ACROREAD_RELEASE}), adobereader-deu" >> adobereader-enu/DEBIAN/control
dpkg-deb -b adobereader-enu . && mv adobereader-enu_${ACROREAD_RELEASE}_i386.deb AdobeReader-enu_${ACROREAD_RELEASE}-1_i386.deb
sed -i 's/^Architecture: i386/Architecture: amd64/' adobereader-enu/DEBIAN/control
dpkg-deb -b adobereader-enu . && mv adobereader-enu_${ACROREAD_RELEASE}_amd64.deb AdobeReader-enu_${ACROREAD_RELEASE}-1_amd64.deb
rm -rf adobereader-enu ${upstream_debfile_enu}

# push new packages into repository

mv AdobeReader-deu_${ACROREAD_RELEASE}-1_i386.deb AdobeReader-deu_${ACROREAD_RELEASE}-1_amd64.deb \
	"$externaptdir"

mv AdobeReader-enu_${ACROREAD_RELEASE}-1_i386.deb AdobeReader-enu_${ACROREAD_RELEASE}-1_amd64.deb \
	"$externaptdir"

cd /var/univention/buildsystem2/apt
apt-ftparchive packages ${release_scope_name}/extern > ${release_scope_name}/extern/Packages
gzip -c ${release_scope_name}/extern/Packages > ${release_scope_name}/extern/Packages.gz
