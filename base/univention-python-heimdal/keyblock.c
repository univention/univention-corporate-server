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

#include <Python.h>

#include <krb5.h>
#include <stdio.h>

#include "error.h"
#include "context.h"
#include "enctype.h"
#include "principal.h"
#include "salt.h"
#include "keyblock.h"

static struct PyMethodDef keyblock_methods[];

krb5KeyblockObject *keyblock_new(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *context;
	krb5EnctypeObject *enctype;
	char *password;
	PyObject *arg;
	if (!PyArg_ParseTuple(args, "OOsO", &context, &enctype, &password,
				&arg))
		return NULL;

	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_New(krb5KeyblockObject, &krb5KeyblockType);
	if (self == NULL)
		return NULL;

	self->context = context->context;

#if PY_MAJOR_VERSION >= 2 && PY_MINOR_VERSION >= 2
	if (PyObject_TypeCheck(arg, &krb5SaltType)) {
		krb5SaltObject *salt = (krb5SaltObject*)arg;
		ret = krb5_string_to_key_salt(context->context, enctype->enctype, password,
				salt->salt, &self->keyblock);
	} else if (PyObject_TypeCheck(arg, &krb5PrincipalType)) {
#else
	if (1) {
#endif
		krb5PrincipalObject *principal = (krb5PrincipalObject*)arg;
		ret = krb5_string_to_key(context->context, enctype->enctype, password,
				principal->principal, &self->keyblock);
	} else {
		PyErr_SetString(PyExc_TypeError, "either principal or salt needs to be passed");
		Py_DECREF(self);
		return NULL;
	}
	if (ret) {
		krb5_exception(NULL, ret);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

krb5KeyblockObject *keyblock_raw_new(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *py_context;
	PyObject *py_enctype;
	PyObject *py_key;
	uint8_t *key_buf;
	size_t key_len;
	krb5_enctype enctype;

	if (!PyArg_ParseTuple(args, "O!OS", &krb5ContextType, &py_context, &py_enctype, &py_key))
		return NULL;

	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_NEW(krb5KeyblockObject, &krb5KeyblockType);
	if (self == NULL)
		return NULL;

	self->context = py_context->context;

	if (PyObject_TypeCheck(py_enctype, &krb5EnctypeType)) {
		krb5EnctypeObject *enctype_obj = (krb5EnctypeObject*)py_enctype;
		enctype = enctype_obj->enctype;
	} else if (PyInt_Check(py_enctype)) {
		enctype = PyInt_AsLong(py_enctype);
	} else {
		PyErr_SetString(PyExc_TypeError, "enctype must be of type integer or krb5EnctypeObject");
		Py_DECREF(self);
		return NULL;
	}

	key_buf = (uint8_t *) PyString_AsString(py_key);
	key_len = PyString_Size(py_key);

	ret = krb5_keyblock_init(py_context->context, enctype, key_buf, key_len, &self->keyblock);

	if (ret) {
		krb5_exception(NULL, ret);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

static PyObject *keyblock_keytype(krb5KeyblockObject *self, PyObject *args)
{
	return (PyObject*) enctype_from_enctype(self->context, self->keyblock.keytype);
}

static PyObject *keyblock_keyvalue(krb5KeyblockObject *self, PyObject *args)
{
	return PyString_FromStringAndSize(self->keyblock.keyvalue.data, self->keyblock.keyvalue.length);
}

static void keyblock_destroy(krb5KeyblockObject *self)
{
	/* FIXME: this segfaults: krb5_free_keyblock(self->context, &self->keyblock); */
	krb5_free_keyblock_contents(self->context, &self->keyblock);
	PyObject_Del(self);
}

static PyObject *keyblock_getattr(krb5KeyblockObject *self, char *name)
{
	return Py_FindMethod(keyblock_methods, (PyObject *)self, name);
}

PyTypeObject krb5KeyblockType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Keyblock",
	sizeof(krb5KeyblockObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)keyblock_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)keyblock_getattr,	/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef keyblock_methods[] = {
	{"keytype", (PyCFunction)keyblock_keytype, METH_VARARGS, "Return keytype"},
	{"keyvalue", (PyCFunction)keyblock_keyvalue, METH_VARARGS, "Return keyvalue"},
	{NULL, NULL, 0, NULL}
};
