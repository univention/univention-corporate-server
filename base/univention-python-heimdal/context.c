/*
 * Python Heimdal
 *	Bindings for the context object of heimdal
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
#include "enctype.h"

static struct PyMethodDef context_methods[];

krb5ContextObject *context_open(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *self = (krb5ContextObject *) PyObject_NEW(krb5ContextObject, &krb5ContextType);
	if (self == NULL)
		return NULL;

	ret = krb5_init_context(&self->context);
	if (ret) {
		Py_DECREF(self);
		krb5_exception(NULL, ret);
		return NULL;
	}

	return self;
}

static PyObject *context_get_permitted_enctypes(krb5ContextObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5_enctype *etypes;
	PyObject* list;
	int i;

	if ((list = PyList_New(0)) == NULL)
		return PyErr_NoMemory();

	ret = krb5_get_permitted_enctypes(self->context, &etypes);
	if (ret) {
		krb5_exception(NULL, ret);
		Py_DECREF(list);
		return NULL;
	}

	for (i=0; etypes && etypes[i] != KRB5_ENCTYPE_NULL; i++) {
		krb5EnctypeObject *enctype;
		enctype = enctype_from_enctype(self->context, etypes[i]);
		PyList_Append(list, (PyObject*) enctype);
		Py_DECREF(enctype);
	}

	return list;
}

static PyObject *context_getattr(krb5ContextObject *self, char *name)
{
	return Py_FindMethod(context_methods, (PyObject *)self, name);
}

static void context_destroy(krb5ContextObject *self)
{
	krb5_free_context(self->context);
	PyObject_Del( self );
}

PyTypeObject krb5ContextType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Context",
	sizeof(krb5ContextObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)context_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)context_getattr,	/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef context_methods[] = {
	{"get_permitted_enctypes", (PyCFunction)context_get_permitted_enctypes, METH_VARARGS, "Return etypes for context"},
	{NULL}
};
