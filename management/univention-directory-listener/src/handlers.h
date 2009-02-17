/*
 * Univention Directory Listener
 *  header information for handlers.c
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

#ifndef _HANDLERS_H_
#define _HANDLERS_H_

#include <sys/types.h>
#include <ldap.h>
#include <python2.4/Python.h>
#include <univention/ldap.h>

#include "cache.h"

/* If HANDLER_INITIALIZED is not set, the module will be initialized.
   If HANDLER_READY is not set, the handler won't be run. Hence, when
   initializing, HANDLER_READY will be set; however, if the
   initialization fails, it will be removed again. If it's successful,
   both, HANDLER_INITIALIZED and HANDLER_READY will be set */
#define HANDLER_INITIALIZED	000000001
#define HANDLER_READY		000000002

#define HANDLER_PREPARED        000000004

#define HANDLER_HAS_FLAG(handler, flag)		((handler->state & flag) == flag)
#define HANDLER_SET_FLAG(handler, flag)		handler->state |= flag
#define HANDLER_UNSET_FLAG(handler, flag)	handler->state &= ~flag

struct filter {
	char	*base;
	int	 scope;
	char	*filter;
};

struct _Handler {
	PyObject	 *module;
	char		 *name;
	char		 *description;
	struct filter	**filters;
	char		**attributes;
	char		*modrdn;
	PyObject	 *handler;
	PyObject	 *initialize;
	PyObject	 *clean;
	PyObject	 *postrun;
	PyObject	 *prerun;
	PyObject	 *setdata; 
	struct _Handler	 *next;

	int		  state;
	int		  prepared : 1;
} typedef Handler;

int	handlers_init			(void);
int	handlers_free_all		(void);
int	handlers_load_path		(char		*filename);
int	handlers_reload_all_paths	(void);
int	handlers_dump			(void);
int	handlers_update			(char		*dn,
					 CacheEntry	*new,
					 CacheEntry	*old,
					 char command);
int	handler_update			(char		*dn,
					 CacheEntry	*new,
					 CacheEntry	*old,
					 Handler	*handler,
					 char command);
int	handlers_delete			(char		*dn,
					 CacheEntry	*old,
					 char command);
int	handler_clean			(Handler	*handler);
int	handlers_clean_all		(void);
int	handler_initialize		(Handler	*handler);
int	handlers_initialize_all		(void);
int	handlers_postrun_all		(void);
int handlers_set_data_all		(char *key, char *value);
char*	handlers_filter			(void);

#endif /* _HANDLERS_H_ */
