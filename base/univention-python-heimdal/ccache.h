/*
 * Python Heimdal
 *	Bindings for the cache API of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __CCACHE_H__
#define __CCACHE_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_ccache ccache;
} krb5CcacheObject;

extern PyTypeObject krb5CcacheType;

krb5CcacheObject *ccache_open(PyObject *unused, PyObject *args);

#endif /* __CCACHE_H__ */
