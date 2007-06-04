/*
 * Univention Password Cache
 *  constants for the password cache modules
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
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
