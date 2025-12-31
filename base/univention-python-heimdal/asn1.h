/*
 * Python Heimdal
 *	Bindings for the ASN.1 API of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __ASN1_H__
#define __ASN1_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>

PyObject* asn1_encode_key(PyObject* args);
PyObject* asn1_decode_key(PyObject *unused, PyObject* args);

#endif /* __ASN1_H__ */
