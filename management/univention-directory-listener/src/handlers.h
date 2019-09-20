/*
 * Univention Directory Listener
 *  header information for handlers.c
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

#ifndef _HANDLERS_H_
#define _HANDLERS_H_

#include <stdbool.h>
#include <sys/types.h>
#include <ldap.h>
#include <python2.7/Python.h>
#include <univention/ldap.h>

#include "cache.h"

/* If HANDLER_INITIALIZED is not set, the module will be initialized.
   If HANDLER_READY is not set, the handler won't be run. Hence, when
   initializing, HANDLER_READY will be set; however, if the
   initialization fails, it will be removed again. If it's successful,
   both, HANDLER_INITIALIZED and HANDLER_READY will be set */
enum state {
	HANDLER_INITIALIZED = 1 << 0,
	HANDLER_READY = 1 << 1,
	HANDLER_PREPARED = 1 << 2,
};

struct filter {
	char *base;
	int scope;
	char *filter;
};

struct _Handler {
	PyObject *module;
	char *name;
	char *description;
	struct filter **filters;
	char **attributes;
	char *modrdn;
	bool handle_every_delete;
	PyObject *handler;
	PyObject *initialize;
	PyObject *clean;
	PyObject *postrun;
	PyObject *prerun;
	PyObject *setdata;
	struct _Handler *next;

	enum state state;
	int prepared : 1;
} typedef Handler;

int handlers_init(void);
int handlers_free_all(void);
void handler_write_state(Handler *handler);
int handlers_load_path(char *filename);
int handlers_reload_all_paths(void);
int handlers_update(const char *dn, CacheEntry *new, CacheEntry *old, char command);
int handler_update(const char *dn, CacheEntry *new, CacheEntry *old, Handler *handler, char command);
int handlers_delete(const char *dn, CacheEntry *old, char command);
int handler_clean(Handler *handler);
int handlers_clean_all(void);
int handler_initialize(Handler *handler);
int handlers_initialize_all(void);
int handlers_postrun_all(void);
int handlers_set_data_all(char *key, char *value);
char *handlers_filter(void);

#endif /* _HANDLERS_H_ */
