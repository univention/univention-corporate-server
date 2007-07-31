/*
 * Univention Directory Listener
 *  header information for change.c
 *
 * Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef _CHANGE_H_
#define _CHANGE_H_

#include <ldap.h>
#include <univention/ldap.h>

#include "network.h"


int	change_new_modules	(univention_ldap_parameters_t	*lp);
int 	change_update_schema	(univention_ldap_parameters_t	*lp);
int	change_update_entry	(univention_ldap_parameters_t	*lp,
				 NotifierID			 id,
				 LDAPMessage			*ldap_entry,
				 char 				command);
int 	change_delete_dn	(NotifierID			 id,
				 char				*dn,
				 char 				command);
int 	change_update_dn	(univention_ldap_parameters_t	*lp,
				 NotifierID			 id,
				 char				*dn,
				 char				command);

#endif /* _CHANGE_H_ */
