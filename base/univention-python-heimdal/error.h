/*
 * Python Heimdal
 *	Bindings for the error handling API of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __ERROR_H__
#define __ERROR_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>

void error_init(PyObject *self);
PyObject *krb5_exception(krb5_context context, int code, ...);

#endif /* __ERROR_H__ */
