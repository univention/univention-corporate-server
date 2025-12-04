/*
 * Python Heimdal
 *	Bindings for the keyblock object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <arpa/inet.h>
#include <krb5.h>
#include <stdio.h>

#include "error.h"
#include "context.h"
#include "enctype.h"
#include "principal.h"
#include "salt.h"
#include "keyblock.h"

krb5KeyblockObject *keyblock_new(PyObject *unused, PyObject *args)
{
	krb5KeyblockObject *self = NULL;
	krb5_error_code err;
	krb5ContextObject *context;
	krb5EnctypeObject *enctype;
	char *password;
	PyObject *arg;

	if (!PyArg_ParseTuple(args, "O!O!sO", &krb5ContextType, &context, &krb5EnctypeType, &enctype, &password, &arg))
		return NULL;

	self = PyObject_New(krb5KeyblockObject, &krb5KeyblockType);
	if (!self)
		return NULL;

	memset(&self->keyblock, 0, sizeof(self->keyblock));

	Py_INCREF(context);
	self->context = context;

	if (PyObject_TypeCheck(arg, &krb5SaltType)) {
		krb5SaltObject *salt = (krb5SaltObject*)arg;

		uint32_t iter = htonl(4096);
		krb5_data opaque = {
			.data = (char *)&iter,
			.length = sizeof(iter)
		};

		err = krb5_string_to_key_salt_opaque(context->context, enctype->enctype, password, salt->salt, opaque, &self->keyblock);
	} else if (PyObject_TypeCheck(arg, &krb5PrincipalType)) {
		krb5PrincipalObject *principal = (krb5PrincipalObject*)arg;
		// TODO also use krb5_string_to_key_salt_opaque here.
		err = krb5_string_to_key(context->context, enctype->enctype, password, principal->principal, &self->keyblock);
	} else {
		PyErr_SetString(PyExc_TypeError, "either principal or salt needs to be passed");
		goto error;
	}

	if (err) {
		krb5_exception(context->context, err);
		goto error;
	}

	return self;

error:
	if (self) {
		krb5_free_keyblock_contents(context->context, &self->keyblock);
		Py_DECREF(self->context);
		PyObject_Del(self);
	}
	return NULL;
}

krb5KeyblockObject *keyblock_raw_new(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	PyObject *py_enctype;
	char *key_data = NULL;
	Py_ssize_t key_len;
	krb5_enctype enctype;

	if (!PyArg_ParseTuple(args, "O!Oy#", &krb5ContextType, &context, &py_enctype, &key_data, &key_len))
		return NULL;

	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_New(krb5KeyblockObject, &krb5KeyblockType);
	if (!self) {
		PyErr_NoMemory();
		return NULL;
	}

	memset(&self->keyblock, 0, sizeof(self->keyblock));
	Py_INCREF(context);
	self->context = context;

	if (PyObject_TypeCheck(py_enctype, &krb5EnctypeType)) {
		krb5EnctypeObject *enctype_obj = (krb5EnctypeObject*)py_enctype;
		enctype = enctype_obj->enctype;
	} else if (PyLong_Check(py_enctype)) {
		enctype = PyLong_AsLong(py_enctype);
		if (PyErr_Occurred()) goto error;
	} else {
		PyErr_SetString(PyExc_TypeError, "enctype must be an integer or krb5EnctypeObject");
		goto error;
	}

	err = krb5_keyblock_init(self->context->context, enctype, key_data, key_len, &self->keyblock);
	if (err) {
		krb5_exception(self->context->context, err);
		goto error;
	}

	return self;

error:
	krb5_free_keyblock_contents(self->context->context, &self->keyblock);
	Py_DECREF(self->context);
	PyObject_Del(self);
	return NULL;
}

static PyObject *keyblock_keytype(krb5KeyblockObject *self)
{
	return (PyObject*) enctype_from_enctype(self->context, self->keyblock.keytype);
}

static PyObject *keyblock_keyvalue(krb5KeyblockObject *self)
{
	return PyBytes_FromStringAndSize(self->keyblock.keyvalue.data, self->keyblock.keyvalue.length);
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
