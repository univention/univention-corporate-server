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
#if 0
#include "realm.h"
#include "ticket.h"
#endif

static struct PyMethodDef module_methods[] = {
	{"context", (PyCFunction)context_open, METH_NOARGS, "Open context"},
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

static const struct types {
	const char *name;
	PyTypeObject *type;
} types[] = {
	{"krb5Ccache", &krb5CcacheType},
	{"krb5Context", &krb5ContextType},
	{"krb5Creds", &krb5CredsType},
	{"krb5Enctype", &krb5EnctypeType},
	{"krb5Keyblock", &krb5KeyblockType},
	{"krb5Keytab", &krb5KeytabType},
	{"krb5Principal", &krb5PrincipalType},
#if 0
	{"krb5Realm", &krb5RealmType},
#endif
	{"krb5Salt", &krb5SaltType},
#if 0
	{"krb5Ticket", &krb5TicketType},
#endif
	{NULL, NULL}
};

static void const_init(PyObject *module) {
	PyModule_AddIntMacro(module, ETYPE_NULL); // 0
	PyModule_AddIntMacro(module, ETYPE_DES_CBC_CRC); // 1
	PyModule_AddIntMacro(module, ETYPE_DES_CBC_MD4); // 2
	PyModule_AddIntMacro(module, ETYPE_DES_CBC_MD5); // 3
	PyModule_AddIntConstant(module, "ETYPE_DES_CBC_RAW", 4);
	PyModule_AddIntMacro(module, ETYPE_DES3_CBC_MD5); // 5
	PyModule_AddIntConstant(module, "ETYPE_DES3_CBC_RAW", 6);
	PyModule_AddIntMacro(module, ETYPE_OLD_DES3_CBC_SHA1); // 7
	PyModule_AddIntMacro(module, ETYPE_SIGN_DSA_GENERATE); // 8
	PyModule_AddIntMacro(module, ETYPE_ENCRYPT_RSA_PRIV); // 9
	PyModule_AddIntMacro(module, ETYPE_ENCRYPT_RSA_PUB); // 10
	PyModule_AddIntConstant(module, "ETYPE_RSA_SHA1_CMS", 11); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_RC2_CBC_ENV", 12); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_RSA_ENV", 13); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_RSA_ES_OEAP_ENV", 14); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_DES_EDE3_CBC_ENV", 15); // ntsecapi.h
	PyModule_AddIntMacro(module, ETYPE_DES3_CBC_SHA1); // 16
	PyModule_AddIntMacro(module, ETYPE_AES128_CTS_HMAC_SHA1_96); // 17
	PyModule_AddIntMacro(module, ETYPE_AES256_CTS_HMAC_SHA1_96); // 18
	PyModule_AddIntMacro(module, ETYPE_AES128_CTS_HMAC_SHA256_128); // 19
	PyModule_AddIntMacro(module, ETYPE_AES256_CTS_HMAC_SHA384_192); // 20
	PyModule_AddIntMacro(module, ETYPE_ARCFOUR_HMAC_MD5); // 23
	PyModule_AddIntMacro(module, ETYPE_ARCFOUR_HMAC_MD5_56); // 24
	PyModule_AddIntConstant(module, "ETYPE_CAMELLIA128_CTS_CMAC", 25);
	PyModule_AddIntConstant(module, "ETYPE_CAMELLIA256_CTS_CMAC", 26);
	PyModule_AddIntMacro(module, ETYPE_ENCTYPE_PK_CROSS); // 48
	PyModule_AddIntConstant(module, "ETYPE_SUBKEY", 65); //
	PyModule_AddIntMacro(module, ETYPE_ARCFOUR_MD4); // -128
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_PLAIN2", -129); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_LM", -130); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_SHA", -131); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_DES_PLAIN", -132); // ntsecapi.h
	PyModule_AddIntMacro(module, ETYPE_ARCFOUR_HMAC_OLD); // -133
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_PLAIN_OLD", -134); // ntsecapi.h
	PyModule_AddIntMacro(module, ETYPE_ARCFOUR_HMAC_OLD_EXP); // -135
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_PLAIN_OLD_EXP", -136); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_PLAIN", -140); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_ARCFOUR_PLAIN_EXP", -141); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_AES128_CTS_HMAC_SHA1_96_PLAIN", -148); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_AES256_CTS_HMAC_SHA1_96_PLAIN", -149); // ntsecapi.h
	PyModule_AddIntConstant(module, "ETYPE_NTLM_HASH", -150); // ntsecapi.h
	PyModule_AddIntMacro(module, ETYPE_DES_CBC_NONE); // -4096
	PyModule_AddIntMacro(module, ETYPE_DES3_CBC_NONE); // -4097
	PyModule_AddIntMacro(module, ETYPE_DES_CFB64_NONE); // -4098
	PyModule_AddIntMacro(module, ETYPE_DES_PCBC_NONE); // -4099
	PyModule_AddIntMacro(module, ETYPE_DIGEST_MD5_NONE); // -4100
	PyModule_AddIntMacro(module, ETYPE_CRAM_MD5_NONE); // -4101
}


static PyObject * moduleinit(void) {
	PyObject *module, *self;
	const struct types *type;
#if PY_MAJOR_VERSION >= 3
	module = PyModule_Create(&moduledef);
#else
	module = Py_InitModule("heimdal", module_methods);
#endif
	if (module == NULL)
		return NULL;

	for (type = types; type->name; type++) {
		if (PyType_Ready(type->type) < 0)
			return NULL;
		Py_INCREF(type->type);
		PyModule_AddObject(module, type->name, (PyObject *)type->type);
	}

	const_init(module);

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
