/*
 * Python Heimdal
 *	Bindings for the ticket object of heimdal
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "ticket.h"

krb5TicketObject *ticket_new(PyObject *unused, PyObject *args)
{
	krb5ContextObject *context;
	if (!PyArg_ParseTuple(args, "O!", &krb5ContextType, &context))
		return NULL;

	krb5TicketObject *self = (krb5TicketObject *) PyObject_New(krb5TicketObject, &krb5TicketType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;

	return self;
}

static void ticket_dealloc(krb5TicketObject *self)
{
	krb5_free_ticket(self->context->context, &self->ticket);
	Py_DECREF(self->context);
	Py_TYPE(self)->tp_free(self);
}

PyTypeObject krb5TicketType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Ticket",
	.tp_doc = "Heimdal Kerberos ticket",
	.tp_basicsize = sizeof(krb5TicketObject),
	/* methods */
	.tp_dealloc = (destructor)ticket_dealloc,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
