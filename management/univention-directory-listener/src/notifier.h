/*
 * Univention LDAP Listener
 *  header information for notifier.c
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef _NOTIFIER_H_
#define _NOTIFIER_H_

#include <univention/ldap.h>
#ifdef WITH_KRB5
#include <univention/krb5.h>
#else
typedef void univention_krb5_parameters_t;
#endif

int	notifier_listen	(univention_ldap_parameters_t	*lp,
			 univention_krb5_parameters_t	*kp,
			 int				 write_transaction_file);

#endif /* _NOTIFIER_H_ */
