/*
 * Python Heimdal
 *	Bindings for the principal object of heimdal
 *
 * Copyright 2003-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "realm.h"
#include "principal.h"

krb5PrincipalObject *principal_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	char *principal_string;

	if (!PyArg_ParseTuple(args, "Os", &context, &principal_string))
		return NULL;

	krb5PrincipalObject *self = (krb5PrincipalObject *) PyObject_New(krb5PrincipalObject, &krb5PrincipalType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;

	err = krb5_parse_name(self->context->context, principal_string, &self->principal);
	if (err) {
		krb5_exception(NULL, err);
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
		krb5_exception(NULL, err);
		return NULL;
	}
	principal = PyString_FromString(principal_string);
	free(principal_string);

	return principal;
}

static PyObject *principal_realm(krb5PrincipalObject *self, PyObject *args)
{
	//krb5_error_code err;
	//krb5_realm *realm;
	PyObject *realm_string;

	//realm = krb5_princ_realm(self->context, self->principal);
	//return realm_from_realm(self->context, realm);
	//realm_string = PyString_FromString(krb5_realm_data(realm));
	realm_string = PyString_FromString("FIXME");
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
	.tp_basicsize = sizeof(krb5PrincipalObject),
	/* methods */
	.tp_dealloc = (destructor)principal_dealloc,
	.tp_str = (reprfunc)principal_name,
	.tp_methods = principal_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
