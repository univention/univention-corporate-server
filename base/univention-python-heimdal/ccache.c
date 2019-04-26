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

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "principal.h"
#include "creds.h"
#include "ccache.h"

static struct PyMethodDef ccache_methods[];

krb5CcacheObject *ccache_open(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *context;
	if (!PyArg_ParseTuple(args, "O", &context))
		return NULL;

	krb5CcacheObject *self = (krb5CcacheObject *) PyObject_NEW(krb5CcacheObject, &krb5CcacheType);
	if (self == NULL)
		return NULL;

	self->context = context->context;

	ret = krb5_cc_default(self->context, &self->ccache);
	if (ret) {
		krb5_exception(self->context, ret);
		Py_DECREF(self);
		return NULL;
	}

#if 0
	ret = krb5_cc_get_principal(self->context, self->ccache, &principal);
	if (ret == ENOENT) {
		error = 1;
		PyErr_SetObject(PyExc_IOError, Py_None);
		goto out;
	} else if (ret)
		krb5_exception(self->context, 1, ret, "krb5_cc_get_principal");
#endif

	return self;
}

static void ccache_close(krb5CcacheObject *self)
{
	krb5_error_code ret;
	ret = krb5_cc_close(self->context, self->ccache);
	if (ret)
		krb5_exception (self->context, 1, ret, "krb5_cc_close");
	PyObject_Del(self);
}

static PyObject *ccache_destroy(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code ret;
	ret = krb5_cc_destroy(self->context, self->ccache);
	if (ret) {
		krb5_exception(self->context, ret, "krb5_cc_destroy");
	}
	PyObject_Del(self);

	Py_RETURN_NONE;
}

static PyObject *ccache_list(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5_cc_cursor cursor;
	krb5_creds creds;
	PyObject *list = NULL;

	ret = krb5_cc_start_seq_get (self->context, self->ccache, &cursor);
	if (ret) {
		krb5_exception(self->context, ret, "krb5_cc_start_seq_get");
		return NULL;
	}

	if ((list = PyList_New(0)) == NULL) {
		krb5_cc_end_seq_get (self->context, self->ccache, &cursor);
		return PyErr_NoMemory();
	}

	while((ret = krb5_cc_next_cred(self->context, self->ccache, &cursor, &creds)) == 0) {
		krb5CredsObject *i;
		i = creds_from_creds(self->context, creds);
		PyList_Append(list, (PyObject *)i);
	}

	ret = krb5_cc_end_seq_get (self->context, self->ccache, &cursor);
	if (ret) {
		Py_DECREF(list);
		krb5_exception(self->context, 1, ret, "krb5_cc_end_seq_get");
		return NULL;
	}

	return list;
}

static PyObject *ccache_initialize(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5PrincipalObject *principal;

	if (!PyArg_ParseTuple(args, "O", &principal))
		return NULL;

	ret = krb5_cc_initialize(self->context, self->ccache, principal->principal);
	if (ret) {
		krb5_exception(self->context, ret);
		return NULL;
	}

	Py_RETURN_NONE;
}

static PyObject *ccache_store_cred(krb5CcacheObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5CredsObject *creds;

	if (!PyArg_ParseTuple(args, "O", &creds))
		return NULL;

	ret = krb5_cc_store_cred(self->context, self->ccache, &creds->creds);
	if (ret) {
		krb5_exception(self->context, ret);
		return NULL;
	}

	Py_RETURN_NONE;
}

static PyObject *ccache_getattr(krb5CcacheObject *self, char *name)
{
	return Py_FindMethod(ccache_methods, (PyObject *)self, name);
}

PyTypeObject krb5CcacheType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"krb5Ccache",			/*tp_name*/
	sizeof(krb5CcacheObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ccache_close,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)ccache_getattr,	/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef ccache_methods[] = {
	{"list", (PyCFunction)ccache_list, METH_VARARGS, "List credentials"},
	{"initialize", (PyCFunction)ccache_initialize, METH_VARARGS, "Initialize credential cache"},
	{"store_cred", (PyCFunction)ccache_store_cred, METH_VARARGS, "Store credentials"},
	{"destroy", (PyCFunction)ccache_destroy, METH_VARARGS, "Destroy credential cache"},
	{NULL, NULL, 0, NULL}
};
