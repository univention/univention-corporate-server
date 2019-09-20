/*
 * Univention Password Cache
 *  constants for the password cache modules
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

#ifndef _PASSWDCACHE_H_
#define _PASSWDCACHE_H_

/* names of cachefiles */
#define PW_DATAFILE "/etc/univention/passwdcache/passwd"
#define SP_DATAFILE "/etc/univention/passwdcache/shadow"
#define GR_DATAFILE "/etc/univention/passwdcache/group"

/* temporary names of cachefiles */
#define PW_DATAFILE_TMP "/etc/univention/passwdcache/passwd.tmp"
#define SP_DATAFILE_TMP "/etc/univention/passwdcache/shadow.tmp"
#define GR_DATAFILE_TMP "/etc/univention/passwdcache/group.tmp"

/* name of lockfile */
#define PWD_LOCK_FILE "/etc/univention/passwdcache/.pwd.lock"


#endif /* _PASSWDCACHE_H_ */
