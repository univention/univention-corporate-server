/*
 * Python Heimdal
 *	Bindings for the principal object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __PRINCIPAL_H__
#define __PRINCIPAL_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_principal principal;
} krb5PrincipalObject;

extern PyTypeObject krb5PrincipalType;

krb5PrincipalObject *principal_new(PyObject *unused, PyObject *args);

#endif /* __PRINCIPAL_H__ */
