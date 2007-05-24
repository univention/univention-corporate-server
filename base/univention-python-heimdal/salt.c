/*
 * Python Heimdal
 *	Bindings for the salt object of heimdal
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
#include "principal.h"
#include "salt.h"

static struct PyMethodDef salt_methods[];

krb5SaltObject *salt_from_salt(krb5_context context, krb5_salt salt)
{
	krb5SaltObject *self = (krb5SaltObject *) PyObject_NEW(krb5SaltObject, &krb5SaltType);

	if (self == NULL)
		return NULL;
	self->context = context;
	self->salt = salt;

	return self;
}


krb5SaltObject *salt_new(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *context;
	krb5PrincipalObject *principal;
	krb5SaltObject *self = (krb5SaltObject *) PyObject_NEW(krb5SaltObject, &krb5SaltType);
	int error = 0;

	if (!PyArg_ParseTuple(args, "OO", &context, &principal))
		return NULL;

	if (self == NULL)
		return NULL;
	self->context = context->context;

	ret = krb5_get_pw_salt(context->context, principal->principal,
			&self->salt);
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

void salt_destroy(krb5SaltObject *self)
{
	krb5_free_salt(self->context, self->salt);
	PyMem_DEL(self);
}

PyTypeObject krb5SaltType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Salt",			/*tp_name*/
	sizeof(krb5SaltObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)salt_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	0,				/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef salt_methods[] = {};
