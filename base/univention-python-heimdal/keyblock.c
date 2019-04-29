/*
 * Python Heimdal
 *	Bindings for the keyblock object of heimdal
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
#include <stdio.h>

#include "error.h"
#include "context.h"
#include "enctype.h"
#include "principal.h"
#include "salt.h"
#include "keyblock.h"

#if PY_MAJOR_VERSION >= 3
#define PyString_FromStringAndSize PyBytes_FromStringAndSize
#endif

krb5KeyblockObject *keyblock_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	krb5EnctypeObject *enctype;
	char *password;
	PyObject *arg;
	if (!PyArg_ParseTuple(args, "O!O!sO", &krb5ContextType, &context, &krb5EnctypeType, &enctype, &password, &arg))
		return NULL;

	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_New(krb5KeyblockObject, &krb5KeyblockType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;

#if PY_MAJOR_VERSION >= 2 && PY_MINOR_VERSION >= 2
	if (PyObject_TypeCheck(arg, &krb5SaltType)) {
		krb5SaltObject *salt = (krb5SaltObject*)arg;
		err = krb5_string_to_key_salt(context->context, enctype->enctype, password,
				salt->salt, &self->keyblock);
	} else if (PyObject_TypeCheck(arg, &krb5PrincipalType)) {
#else
	if (1) {
#endif
		krb5PrincipalObject *principal = (krb5PrincipalObject*)arg;
		err = krb5_string_to_key(context->context, enctype->enctype, password,
				principal->principal, &self->keyblock);
	} else {
		PyErr_SetString(PyExc_TypeError, "either principal or salt needs to be passed");
		Py_DECREF(self);
		return NULL;
	}
	if (err) {
		krb5_exception(self->context->context, err);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

krb5KeyblockObject *keyblock_raw_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	PyObject *py_enctype;
	char *key_data = NULL;
	Py_ssize_t key_len;
	krb5_enctype enctype;

#if PY_MAJOR_VERSION >= 3
	if (!PyArg_ParseTuple(args, "O!Oy#", &krb5ContextType, &context, &py_enctype, &key_data, &key_len))
#else
	if (!PyArg_ParseTuple(args, "O!Os#", &krb5ContextType, &context, &py_enctype, &key_data, &key_len))
#endif
		return NULL;

	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_NEW(krb5KeyblockObject, &krb5KeyblockType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;

	if (PyObject_TypeCheck(py_enctype, &krb5EnctypeType)) {
		krb5EnctypeObject *enctype_obj = (krb5EnctypeObject*)py_enctype;
		enctype = enctype_obj->enctype;
#if PY_MAJOR_VERSION >= 3
	} else if (PyLong_Check(py_enctype)) {
		enctype = PyLong_AsLong(py_enctype);
#else
	} else if (PyInt_Check(py_enctype)) {
		enctype = PyInt_AsLong(py_enctype);
#endif
	} else {
		PyErr_SetString(PyExc_TypeError, "enctype must be of type integer or krb5EnctypeObject");
		Py_DECREF(self);
		return NULL;
	}

	err = krb5_keyblock_init(self->context->context, enctype, key_data, key_len, &self->keyblock);

	if (err) {
		krb5_exception(self->context->context, err);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

static PyObject *keyblock_keytype(krb5KeyblockObject *self)
{
	return (PyObject*) enctype_from_enctype(self->context, self->keyblock.keytype);
}

static PyObject *keyblock_keyvalue(krb5KeyblockObject *self)
{
	return PyString_FromStringAndSize(self->keyblock.keyvalue.data, self->keyblock.keyvalue.length);
}

static void keyblock_dealloc(krb5KeyblockObject *self)
{
	/* FIXME: this segfaults: krb5_free_keyblock(self->context->context, &self->keyblock); */
	krb5_free_keyblock_contents(self->context->context, &self->keyblock);
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef keyblock_methods[] = {
	{"keytype", (PyCFunction)keyblock_keytype, METH_NOARGS, "Return keytype"},
	{"keyvalue", (PyCFunction)keyblock_keyvalue, METH_NOARGS, "Return keyvalue"},
	{NULL}
};

PyTypeObject krb5KeyblockType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Keyblock",
	.tp_doc = "Heimdal Kerberos key block",
	.tp_basicsize = sizeof(krb5KeyblockObject),
	/* methods */
	.tp_dealloc = (destructor)keyblock_dealloc,
	.tp_methods = keyblock_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
