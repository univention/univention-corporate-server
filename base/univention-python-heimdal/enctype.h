/*
 * Python Heimdal
 *	Bindings for the encryption API of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __ENCTYPE_H__
#define __ENCTYPE_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_enctype enctype;
} krb5EnctypeObject;

extern PyTypeObject krb5EnctypeType;

krb5EnctypeObject *enctype_new(PyObject *unused, PyObject *args);
krb5EnctypeObject *enctype_from_enctype(krb5ContextObject *context, krb5_enctype enctype);

#endif /* __ENCTYPE_H__ */
