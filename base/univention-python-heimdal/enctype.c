/*
 * Python Heimdal
 *	Bindings for the encryption API of heimdal
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
#include "enctype.h"

#if PY_MAJOR_VERSION >= 3
#define PyInt_FromLong PyLong_FromLong
#define PyString_FromString PyUnicode_FromString
#endif

krb5EnctypeObject *enctype_from_enctype(krb5ContextObject *context, krb5_enctype enctype)
{
	krb5EnctypeObject *self = (krb5EnctypeObject *) PyObject_NEW(krb5EnctypeObject, &krb5EnctypeType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;
	self->enctype = enctype;

	return self;
}

krb5EnctypeObject *enctype_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	char *enctype_string;
	if (!PyArg_ParseTuple(args, "O!s", &krb5ContextType, &context, &enctype_string))
		return NULL;

	krb5EnctypeObject *self = (krb5EnctypeObject *) PyObject_NEW(krb5EnctypeObject, &krb5EnctypeType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;

	err = krb5_string_to_enctype(context->context, enctype_string,
			&self->enctype);
	if (err) {
		Py_DECREF(self);
		krb5_exception(self->context->context, err);
		return NULL;
	}

	return self;
}

static PyObject *enctype_string(krb5EnctypeObject *self)
{
	krb5_error_code err;
	char *enctype_c_string;
	PyObject *enctype_string;

	err = krb5_enctype_to_string(self->context->context, self->enctype, &enctype_c_string);
	if (err) {
		krb5_exception(self->context->context, err);
		return NULL;
	}
	enctype_string = PyString_FromString(enctype_c_string);
	free(enctype_c_string);

	return enctype_string;
}

static PyObject *enctype_int(krb5EnctypeObject *self)
{
	return PyInt_FromLong(self->enctype);
}

static void enctype_dealloc(krb5EnctypeObject *self)
{
	/* enctype really is integer; nothing to free */
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef enctype_methods[] = {
	{"toint", (PyCFunction)enctype_int, METH_NOARGS, "Convert enctype to integer"},
	{NULL}
};

PyTypeObject krb5EnctypeType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Enctype",
	.tp_doc = "Heimdal Kerberos encryption type",
	.tp_basicsize = sizeof(krb5EnctypeObject),
	/* methods */
	.tp_dealloc = (destructor)enctype_dealloc,
	.tp_str = (reprfunc)enctype_string,
	.tp_methods = enctype_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
