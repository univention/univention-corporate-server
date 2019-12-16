/*
 * Python Heimdal
 *	Bindings for the cache API of heimdal
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
#include "creds.h"
#include "ccache.h"

krb5CcacheObject *ccache_open(PyObject *unused, PyObject *args)
{
	krb5_error_code err;
	krb5ContextObject *context;
	if (!PyArg_ParseTuple(args, "O!", &krb5ContextType, &context))
		return NULL;

	krb5CcacheObject *self = (krb5CcacheObject *) PyObject_NEW(krb5CcacheObject, &krb5CcacheType);
	if (self == NULL) {
		PyErr_NoMemory();
		return NULL;
	}

	Py_INCREF(context);
	self->context = context;

	self->ccache = NULL;
	err = krb5_cc_default(self->context->context, &self->ccache);
	if (err) {
		krb5_exception(self->context->context, err);
		Py_DECREF(self);
		return NULL;
	}

#if 0
	err = krb5_cc_get_principal(self->context->context, self->ccache, &principal);
	if (err == ENOENT) {
		error = 1;
		PyErr_SetObject(PyExc_IOError, Py_None);
		goto out;
	} else if (err)
		krb5_exception(self->context->context, err, "krb5_cc_get_principal");
#endif

	return self;
}

static void ccache_dealloc(krb5CcacheObject *self)
{
	if (self->ccache) {
		krb5_error_code err = krb5_cc_close(self->context->context, self->ccache);
		self->ccache = NULL;
		if (err)
			krb5_exception(self->context->context, err, "krb5_cc_close");
	}
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

static PyObject *ccache_destroy(krb5CcacheObject *self)
{
	if (self->ccache) {
		krb5_error_code err = krb5_cc_destroy(self->context->context, self->ccache);
		self->ccache = NULL;
		if (err)
			krb5_exception(self->context->context, err, "krb5_cc_destroy");
	}

	Py_RETURN_NONE;
}

static PyObject *ccache_list(krb5CcacheObject *self)
{
	krb5_error_code err;
	krb5_cc_cursor cursor;
	krb5_creds creds;
	PyObject *list = NULL;

	if (!self->ccache) {
		krb5_exception(NULL, ENOENT);
		return NULL;
	}

	err = krb5_cc_start_seq_get (self->context->context, self->ccache, &cursor);
	if (err) {
		krb5_exception(self->context->context, err, "krb5_cc_start_seq_get");
		return NULL;
	}

	if ((list = PyList_New(0)) == NULL) {
		krb5_cc_end_seq_get (self->context->context, self->ccache, &cursor);
		return PyErr_NoMemory();
	}

	while((err = krb5_cc_next_cred(self->context->context, self->ccache, &cursor, &creds)) == 0) {
		krb5CredsObject *i;
		i = creds_from_creds(self->context, creds);
		PyList_Append(list, (PyObject *)i);
		Py_DECREF(i);
	}

	err = krb5_cc_end_seq_get (self->context->context, self->ccache, &cursor);
	if (err) {
		Py_DECREF(list);
		krb5_exception(self->context->context, err, "krb5_cc_end_seq_get");
		return NULL;
	}

	return list;
}

static PyObject *ccache_initialize(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code err;
	krb5PrincipalObject *principal;

	if (!self->ccache) {
		krb5_exception(NULL, ENOENT);
		return NULL;
	}

	if (!PyArg_ParseTuple(args, "O!", &krb5PrincipalType, &principal))
		return NULL;

	err = krb5_cc_initialize(self->context->context, self->ccache, principal->principal);
	if (err) {
		krb5_exception(self->context->context, err);
		return NULL;
	}

	Py_RETURN_NONE;
}

static PyObject *ccache_store_cred(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code err;
	krb5CredsObject *creds;

	if (!PyArg_ParseTuple(args, "O!", &krb5CredsType, &creds))
		return NULL;

	err = krb5_cc_store_cred(self->context->context, self->ccache, &creds->creds);
	if (err) {
		krb5_exception(self->context->context, err);
		return NULL;
	}

	Py_RETURN_NONE;
}

static struct PyMethodDef ccache_methods[] = {
	{"list", (PyCFunction)ccache_list, METH_NOARGS, "List credentials"},
	{"initialize", (PyCFunction)ccache_initialize, METH_VARARGS, "Initialize credential cache"},
	{"store_cred", (PyCFunction)ccache_store_cred, METH_VARARGS, "Store credentials"},
	{"destroy", (PyCFunction)ccache_destroy, METH_NOARGS, "Destroy credential cache"},
	{NULL}
};

PyTypeObject krb5CcacheType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Ccache",
	.tp_doc = "Heimdal Kerberos credential cache",
	.tp_basicsize = sizeof(krb5CcacheObject),
	/* methods */
	.tp_dealloc = (destructor)ccache_dealloc,
	.tp_methods = ccache_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
