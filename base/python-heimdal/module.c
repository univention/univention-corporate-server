/*
 * Python Heimdal
 *	module definitions for the heimdal python bindungs
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

#include "error.h"
#include "context.h"
#include "principal.h"
#include "creds.h"
#include "keytab.h"
#include "ccache.h"
#include "salt.h"
#include "enctype.h"
#include "keyblock.h"
#include "asn1.h"

static struct PyMethodDef module_methods[] = {
	{"context", (PyCFunction)context_open, METH_VARARGS, "Open context"},
	{"principal", (PyCFunction)principal_new, METH_VARARGS, "New principal"},
	{"creds", (PyCFunction)creds_new, METH_VARARGS, "New credentials"},
	{"keytab", (PyCFunction)keytab_open, METH_VARARGS, "Open keytab"},
	{"ccache", (PyCFunction)ccache_open, METH_VARARGS, "Open credential cache"},
	{"salt", (PyCFunction)salt_new, METH_VARARGS, "Create new salt"},
	{"enctype", (PyCFunction)enctype_new, METH_VARARGS, "Create enctype"},
	{"keyblock", (PyCFunction)keyblock_new, METH_VARARGS, "Create keyblock"},
	{"asn1_encode_key", (PyCFunction)asn1_encode_key, METH_VARARGS, "ASN1 encode keyblock"},
	{NULL, NULL, 0, NULL}
};

void initheimdal(void)
{
	PyObject *module, *self;
	module = Py_InitModule("heimdal", module_methods);
	self = PyModule_GetDict(module);

	error_init(self);
}
