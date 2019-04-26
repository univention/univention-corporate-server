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
#endif

static PyObject * moduleinit(void) {
	PyObject *module, *self;
#if PY_MAJOR_VERSION >= 3
	module = PyModule_Create(&moduledef);
#else
	module = Py_InitModule("heimdal", module_methods);
#endif
	if (module == NULL)
		return NULL;

	if (PyType_Ready(&krb5CcacheType) < 0)
		return NULL;
	if (PyType_Ready(&krb5ContextType) < 0)
		return NULL;
	if (PyType_Ready(&krb5CredsType) < 0)
		return NULL;
	if (PyType_Ready(&krb5EnctypeType) < 0)
		return NULL;
	if (PyType_Ready(&krb5KeyblockType) < 0)
		return NULL;
	if (PyType_Ready(&krb5KeytabType) < 0)
		return NULL;
	if (PyType_Ready(&krb5PrincipalType) < 0)
		return NULL;
#if 0
	if (PyType_Ready(&krb5RealmType) < 0)
		return NULL;
#endif
	if (PyType_Ready(&krb5SaltType) < 0)
		return NULL;
#if 0
	if (PyType_Ready(&krb5TicketType) < 0)
		return NULL;
#endif

	self = PyModule_GetDict(module);
	error_init(self);

	return module;
}

#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_heimdal(void) {
	return moduleinit();
}
#else
PyMODINIT_FUNC initheimdal(void) {
	moduleinit();
}
#endif
