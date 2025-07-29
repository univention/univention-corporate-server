/*
 * Python Heimdal
 *	Bindings for the keyblock object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __KEYBLOCK_H__
#define __KEYBLOCK_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_keyblock keyblock;
} krb5KeyblockObject;

extern PyTypeObject krb5KeyblockType;

krb5KeyblockObject *keyblock_new(PyObject *unused, PyObject *args);
krb5KeyblockObject *keyblock_raw_new(PyObject *unused, PyObject *args);

#endif /* __KEYBLOCK_H__ */
