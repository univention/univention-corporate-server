/*
 * Python Heimdal
 *	module definitions for the heimdal python bindungs
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
	{"salt_raw", (PyCFunction)salt_raw_new, METH_VARARGS, "Create new salt from a string"},
	{"enctype", (PyCFunction)enctype_new, METH_VARARGS, "Create enctype"},
	{"keyblock", (PyCFunction)keyblock_new, METH_VARARGS, "Create keyblock"},
	{"keyblock_raw", (PyCFunction)keyblock_raw_new, METH_VARARGS, "Create a keyblock from an existing blob"},
	{"asn1_encode_key", (PyCFunction)asn1_encode_key, METH_VARARGS, "ASN1 encode keyblock"},
	{"asn1_decode_key", (PyCFunction)asn1_decode_key, METH_VARARGS, "ASN1 decode keyblock"},
	{NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	.m_name = "heimdal",
	.m_doc = "Heimdal Kerberos Python binding",
	.m_size = -1,
	.m_methods = module_methods,
};

PyMODINIT_FUNC PyInit_heimdal(void) {
	PyObject *module, *self;
	module = PyModule_Create(&moduledef);
	if (module == NULL)
		return NULL;

	self = PyModule_GetDict(module);
	error_init(self);

	return module;
}
#else
PyMODINIT_FUNC
initheimdal(void)
{
	PyObject *module, *self;
	module = Py_InitModule("heimdal", module_methods);
	if (module == NULL)
		return;

	self = PyModule_GetDict(module);
	error_init(self);
}
#endif
