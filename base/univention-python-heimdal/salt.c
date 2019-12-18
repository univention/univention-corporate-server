/*
 * Python Heimdal
 *	Bindings for the salt object of heimdal
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

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "principal.h"
#include "salt.h"

#if PY_MAJOR_VERSION >= 3
#define PyString_FromStringAndSize PyUnicode_FromStringAndSize
#endif

#if 0
krb5SaltObject *salt_from_salt(krb5ContextObject *context, krb5_salt salt)
{
	krb5SaltObject *self = (krb5SaltObject *) PyObject_New(krb5SaltObject, &krb5SaltType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;
	self->salt = salt;

	return self;
}
#endif

krb5SaltObject *salt_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	krb5PrincipalObject *principal;

	if (!PyArg_ParseTuple(args, "O!O!", &krb5ContextType, &context, &krb5PrincipalType, &principal))
		return NULL;

	krb5SaltObject *self = (krb5SaltObject *) PyObject_NEW(krb5SaltObject, &krb5SaltType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;

	err = krb5_get_pw_salt(context->context, principal->principal,
			&self->salt);
	if (err) {
		krb5_exception(self->context->context, err);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

krb5SaltObject *salt_raw_new(PyObject *unused, PyObject *args) {
	krb5ContextObject *context;
	char *saltstring = NULL;
	Py_ssize_t saltlen;

	if (!PyArg_ParseTuple(args, "O!s#", &krb5ContextType, &context, &saltstring, &saltlen))
		return NULL;

	krb5SaltObject *self = (krb5SaltObject *) PyObject_NEW(krb5SaltObject, &krb5SaltType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;
	self->salt.salttype = KRB5_PW_SALT;
	self->salt.saltvalue.length = saltlen;
	self->salt.saltvalue.data = strdup(saltstring);

	return self;
}

static PyObject *salt_saltvalue(krb5SaltObject *self, PyObject *args)
{
	return PyString_FromStringAndSize(self->salt.saltvalue.data, self->salt.saltvalue.length);
}

static void salt_dealloc(krb5SaltObject *self)
{
	krb5_free_salt(self->context->context, self->salt);
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef salt_methods[] = {
	{"saltvalue", (PyCFunction)salt_saltvalue, METH_VARARGS, "Return saltvalue"},
	{NULL, NULL, 0, NULL}
};

PyTypeObject krb5SaltType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Salt",
	.tp_doc = "Heimdal Kerberos salt",
	.tp_basicsize = sizeof(krb5SaltObject),
	/* methods */
	.tp_dealloc = (destructor)salt_dealloc,
	.tp_methods = salt_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
