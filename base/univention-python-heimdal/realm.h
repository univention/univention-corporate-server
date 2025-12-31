/*
 * Python Heimdal
 *	Bindings for the realm object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __REALM_H__
#define __REALM_H__

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <krb5.h>
#include "context.h"

typedef struct {
	PyObject_HEAD
	krb5ContextObject *context;
	krb5_realm *realm;
} krb5RealmObject;

extern PyTypeObject krb5RealmType;

#if 0
krb5RealmObject *realm_from_realm(krb5ContextObject *context, krb5_realm *realm);
#endif

#endif /* __REALM_H__ */
