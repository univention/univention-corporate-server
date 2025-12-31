/*
 * Python Heimdal
 *	Bindings for the salt object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __SALT_H__
#define __SALT_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_salt salt;
} krb5SaltObject;

extern PyTypeObject krb5SaltType;

krb5SaltObject *salt_new(PyObject *unused, PyObject *args);
krb5SaltObject *salt_raw_new(PyObject *unused, PyObject *args);
#if 0
krb5SaltObject *salt_from_salt(krb5ContextObject *context, krb5_salt salt);
#endif

#endif /* __SALT_H__ */
