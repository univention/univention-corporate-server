/*
 * Python Heimdal
 *	Bindings for the credentials API of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __CREDS_H__
#define __CREDS_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_creds creds;
} krb5CredsObject;

extern PyTypeObject krb5CredsType;

krb5CredsObject *creds_from_creds(krb5ContextObject *context, krb5_creds creds);
krb5CredsObject *creds_new(PyObject *unused, PyObject *args);

#endif /* __CREDS_H__ */
