/*
 * Python Heimdal
 *	Bindings for the keyblock object of heimdal
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
	krb5KeyblockObject *self = (krb5KeyblockObject *) PyObject_NEW(krb5KeyblockObject, &krb5KeyblockType);
	int error = 0;

	if (!PyArg_ParseTuple(args, "OOsO", &context, &enctype, &password,
				&arg))
		return NULL;

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
		error = 1;
		goto out;
	}
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

PyObject *keyblock_keytype(krb5KeyblockObject *self, PyObject *args)
{
	return (PyObject*) enctype_from_enctype(self->context, self->keyblock.keytype);
}

PyObject *keyblock_keyvalue(krb5KeyblockObject *self, PyObject *args)
{
	return PyString_FromString(self->keyblock.keyvalue.data);
}

void keyblock_destroy(krb5KeyblockObject *self)
{
	/* FIXME: this segfaults: krb5_free_keyblock(self->context, &self->keyblock); */
	krb5_free_keyblock_contents(self->context, &self->keyblock);
	PyMem_DEL(self);
}

static PyObject *keyblock_getattr(krb5KeyblockObject *self, char *name)
{
	return Py_FindMethod(keyblock_methods, (PyObject *)self, name);
}

PyTypeObject krb5KeyblockType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Keyblock",			/*tp_name*/
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
