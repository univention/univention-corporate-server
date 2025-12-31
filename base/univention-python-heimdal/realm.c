/*
 * Python Heimdal
 *	Bindings for the realm object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "realm.h"

#if 0
krb5RealmObject *realm_from_realm(krb5ContextObject *context, krb5_realm *realm)
{
	krb5RealmObject *self = (krb5RealmObject *) PyObject_New(krb5RealmObject, &krb5RealmType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;
	self->realm = realm;

	return self;
}
#endif

static void realm_dealloc(krb5RealmObject *self)
{
#if 0
	Py_DECREF(self->context);
#endif
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef realm_methods[] = {
	{NULL},
};

PyTypeObject krb5RealmType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Realm",
	.tp_doc = "Heimdal Kerberos realm",
	.tp_basicsize = sizeof(krb5RealmObject),
	/* methods */
	.tp_dealloc = (destructor)realm_dealloc,
	.tp_methods = realm_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
