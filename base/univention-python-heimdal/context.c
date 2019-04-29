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

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "enctype.h"

krb5ContextObject *context_open(PyObject *unused)
{
	return (krb5ContextObject *)PyObject_CallObject((PyObject *)&krb5ContextType, NULL);
}

static PyObject *context_get_permitted_enctypes(krb5ContextObject *self)
{
	krb5_error_code err;
	krb5_enctype *etypes = NULL;
	PyObject* list = NULL;
	int i;

	err = krb5_get_permitted_enctypes(self->context, &etypes);
	if (err) {
		krb5_exception(self->context, err);
		goto exception;
	}

	for (i = 0; etypes && etypes[i] != KRB5_ENCTYPE_NULL; i++)
		;

	if ((list = PyList_New(i)) == NULL) {
		PyErr_NoMemory();
		goto exception;
	}

	while (i--) {
		krb5EnctypeObject *enctype;
		enctype = enctype_from_enctype(self, etypes[i]);
		if (enctype == NULL) {
			goto exception;
		}
		PyList_SetItem(list, i, (PyObject *)enctype);
	}
	goto finally;

exception:
	Py_XDECREF(list);
	list = NULL;
finally:
	if (etypes)
#if 0
		krb5_free_enctypes(self->context, etypes);
#else
		free(etypes);
#endif
	return list;
}

static PyObject *context_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	krb5ContextObject *self = (krb5ContextObject *)type->tp_alloc(type, 0);
	return (PyObject *)self;
}

static int context_init(krb5ContextObject *self, PyObject *args, PyObject *kwds)
{
	if (self->context) {
		krb5_free_context(self->context);
		self->context = NULL;
	}
	krb5_error_code err = krb5_init_context(&self->context);
	if (err) {
		return -1;
	}
	return 0;
}

static void context_dealloc(krb5ContextObject *self)
{
	krb5_free_context(self->context);
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef context_methods[] = {
	{"get_permitted_enctypes", (PyCFunction)context_get_permitted_enctypes, METH_NOARGS, "Return etypes for context"},
	{NULL}
};

PyTypeObject krb5ContextType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Context",
	.tp_doc = "Heimdal Kerberos context",
	.tp_basicsize = sizeof(krb5ContextObject),
	/* methods */
	.tp_dealloc = (destructor)context_dealloc,
	.tp_methods = context_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_init = (initproc)context_init,
	.tp_new = context_new,
};
