/*
 * Python Heimdal
 *	Bindings for the ticket object of heimdal
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
#include "ticket.h"

krb5TicketObject *ticket_new(PyObject *unused, PyObject *args)
{
	krb5ContextObject *context;
	krb5TicketObject *self = (krb5TicketObject *) PyObject_NEW(krb5TicketObject, &krb5TicketType);

	if (!PyArg_ParseTuple(args, "O", &context))
		return NULL;

	if (self == NULL)
		return NULL;
	self->context = context->context;

	return self;
}

void ticket_destroy(krb5TicketObject *self)
{
	krb5_free_ticket(self->context, &self->ticket);
	PyMem_DEL(self);
}

PyTypeObject krb5TicketType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Ticket",			/*tp_name*/
	sizeof(krb5TicketObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ticket_destroy,	/*tp_dealloc*/
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

static struct PyMethodDef ticket_methods[] = {};
