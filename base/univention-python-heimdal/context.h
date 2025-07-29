/*
 * Python Heimdal
 *	Bindings for the context object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __CONTEXT_H__
#define __CONTEXT_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>

typedef struct {
	PyObject_HEAD
	krb5_context context;
} krb5ContextObject;

extern PyTypeObject krb5ContextType;

krb5ContextObject *context_open(PyObject *unused);

#endif /* __CONTEXT_H__ */
