#!/bin/bash

# Copyright 2015 Univention GmbH
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

DATE="${1:?Missing argument: date for file/directory names}"

if ! ls app/*.ini > /dev/null; then
	echo "ERROR: Please start from package directory."
	exit 1
fi

scp app/*.meta app/*_screenshot.* app/*_$DATE.{ini,png} omar:/mnt/omar/vmwares/mirror/appcenter.test/meta-inf/4.1/self-service/
ssh omar mkdir       /mnt/omar/vmwares/mirror/appcenter.test/univention-repository/4.1/maintained/component/self-service_$DATE
scp app/README* omar:/mnt/omar/vmwares/mirror/appcenter.test/univention-repository/4.1/maintained/component/self-service_$DATE/

