/*
 * Python Heimdal
 *	Bindings for the principal object of heimdal
 *
 * Copyright (C) 2003, 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "realm.h"
#include "principal.h"

static struct PyMethodDef principal_methods[];

krb5PrincipalObject *principal_new(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *context;
	char *principal_string;
	krb5PrincipalObject *self = (krb5PrincipalObject *) PyObject_NEW(krb5PrincipalObject, &krb5PrincipalType);
	int error = 0;

	if (!PyArg_ParseTuple(args, "Os", &context, &principal_string))
		return NULL;

	if (self == NULL)
		return NULL;
	self->context = context->context;

	ret = krb5_parse_name(self->context, principal_string, &self->principal);
	if (ret) {
		error = 1;
		krb5_exception(NULL, ret);
		goto out;
	}

 out:
	if (error)
		return NULL;
	else
		return self;
}

PyObject *principal_name(krb5PrincipalObject *self)
{
	krb5_error_code ret;
	char *principal_string;
	PyObject *principal;
	int error = 0;

	ret = krb5_unparse_name(self->context, self->principal, &principal_string);
	if (ret) {
		error = 1;
		krb5_exception(NULL, ret);
		goto out;
	}
	principal = PyString_FromString(principal_string);
	free(principal_string);

 out:
	if (error)
		return NULL;
	else
		return principal;
}

PyObject *principal_realm(krb5PrincipalObject *self, PyObject *args)
{
	//krb5_error_code ret;
	//krb5_realm *realm;
	PyObject *realm_string;

	//realm = krb5_princ_realm(self->context, self->principal);
	//return realm_from_realm(self->context, realm);
	//realm_string = PyString_FromString(krb5_realm_data(realm));
	realm_string = PyString_FromString("FIXME");
	return realm_string;
}

void principal_destroy(krb5PrincipalObject *self)
{
	krb5_free_principal(self->context, self->principal);
	PyMem_DEL(self);
}

static PyObject *principal_getattr(krb5PrincipalObject *self, char *name)
{
	return Py_FindMethod(principal_methods, (PyObject *)self, name);
}

PyTypeObject krb5PrincipalType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Principal",		/*tp_name*/
	sizeof(krb5PrincipalObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)principal_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)principal_getattr,	/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	(reprfunc)principal_name,	/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef principal_methods[] = {
	{"realm", (PyCFunction)principal_realm, METH_VARARGS, "Return realm of principal"},
	{NULL}
};
