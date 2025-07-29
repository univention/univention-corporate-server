/*
 * Univention Directory Listener
 *  header information for handlers.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _HANDLERS_H_
#define _HANDLERS_H_

#include <stdbool.h>
#include <sys/types.h>
#include <ldap.h>
#include <python3.11/Python.h>
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
	bool modrdn;
	bool handle_every_delete;
	PyObject *handler;
	PyObject *initialize;
	PyObject *clean;
	PyObject *postrun;
	PyObject *prerun;
	PyObject *setdata;
	double priority;
	struct _Handler *next;

	enum state state;
	int prepared : 1;
} typedef Handler;

#define PRIORITY_MINIMUM 0.0
#define PRIORITY_DEFAULT 50.0
#define PRIORITY_MAXIMUM 100.0

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
