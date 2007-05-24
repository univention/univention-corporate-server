/*
 * Python Heimdal
 *	Bindings for the context object of heimdal
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

static struct PyMethodDef context_methods[];

krb5ContextObject *context_open(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *self = (krb5ContextObject *) PyObject_NEW(krb5ContextObject, &krb5ContextType);
	int error = 0;

	if (self == NULL)
		return NULL;

	ret = krb5_init_context(&self->context);
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

PyObject *context_get_default_in_tkt_etypes(krb5ContextObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5_enctype *etypes;
	PyObject* list;
	int i;
	int error = 0;

	if ((list = PyList_New(0)) == NULL) {
		/* FIXME: raise exception */
		error = 1;
		goto out;
	}

	ret = krb5_get_default_in_tkt_etypes(self->context, &etypes);
	if (ret) {
		error = 1;
		krb5_exception(NULL, ret);
		goto out;
	}

	for (i=0; etypes && etypes[i] != ETYPE_NULL; i++) {
		krb5EnctypeObject *enctype;
		enctype = enctype_from_enctype(self->context, etypes[i]);
		PyList_Append(list, (PyObject*) enctype);
		Py_DECREF(enctype);
	}

 out:
	if (error)
		return NULL;
	else
		return list;
}

static PyObject *context_getattr(krb5ContextObject *self, char *name)
{
	return Py_FindMethod(context_methods, (PyObject *)self, name);
}

void context_destroy(krb5ContextObject *self)
{
	krb5_free_context(self->context);
	PyMem_DEL(self);
}

PyTypeObject krb5ContextType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Context",			/*tp_name*/
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
	{"get_default_in_tkt_etypes", (PyCFunction)context_get_default_in_tkt_etypes, METH_VARARGS, "Return etypes for context"},
	{NULL}
};
