/*
 * Python Heimdal
 *	Bindings for the principal object of heimdal
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
#include "principal.h"

#if PY_MAJOR_VERSION >= 3
#define PyString_FromString PyUnicode_FromString
#endif

krb5PrincipalObject *principal_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	char *principal_string;

	if (!PyArg_ParseTuple(args, "O!s", &krb5ContextType, &context, &principal_string))
		return NULL;

	krb5PrincipalObject *self = (krb5PrincipalObject *) PyObject_New(krb5PrincipalObject, &krb5PrincipalType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;

	err = krb5_parse_name(self->context->context, principal_string, &self->principal);
	if (err) {
		krb5_exception(self->context->context, err);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

static PyObject *principal_name(krb5PrincipalObject *self)
{
	krb5_error_code err;
	char *principal_string;
	PyObject *principal;

	err = krb5_unparse_name(self->context->context, self->principal, &principal_string);
	if (err) {
		krb5_exception(self->context->context, err);
		return NULL;
	}
	principal = PyString_FromString(principal_string);
	free(principal_string);

	return principal;
}

static PyObject *principal_realm(krb5PrincipalObject *self, PyObject *args)
{
	const char *realm;
	PyObject *realm_string;

	realm = krb5_principal_get_realm(self->context->context, self->principal);
	realm_string = PyString_FromString(realm);
	return realm_string;
}

static void principal_dealloc(krb5PrincipalObject *self)
{
	krb5_free_principal(self->context->context, self->principal);
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef principal_methods[] = {
	{"realm", (PyCFunction)principal_realm, METH_VARARGS, "Return realm of principal"},
	{NULL}
};

PyTypeObject krb5PrincipalType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Principal",
	.tp_doc = "Heimdal Kerberos principal",
	.tp_basicsize = sizeof(krb5PrincipalObject),
	/* methods */
	.tp_dealloc = (destructor)principal_dealloc,
	.tp_str = (reprfunc)principal_name,
	.tp_methods = principal_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
