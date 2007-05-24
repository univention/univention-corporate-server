/*
 * Python Heimdal
 *	Bindings for the realm object of heimdal
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
#include "realm.h"

krb5RealmObject *realm_from_realm(krb5_context context, krb5_realm *realm)
{
	krb5RealmObject *self = (krb5RealmObject *) PyObject_NEW(krb5RealmObject, &krb5RealmType);

	self->context = context;
	self->realm = realm;

	return self;
}

void realm_destroy(krb5RealmObject *self)
{
	PyMem_DEL(self);
}

PyTypeObject krb5RealmType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Realm",			/*tp_name*/
	sizeof(krb5RealmObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)realm_destroy,	/*tp_dealloc*/
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

static struct PyMethodDef realm_methods[] = {};
