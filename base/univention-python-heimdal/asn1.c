/*
 * Python Heimdal
 *	Bindings for the ASN.1 API of heimdal
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
#include <hdb.h>

#include "keyblock.h"
#include "context.h"
#include "salt.h"
#include "error.h"

#if PY_MAJOR_VERSION >= 3
#define PyString_FromStringAndSize PyBytes_FromStringAndSize
#endif

/*
In case you are looking into some problem here, note that asn1_Key.c and asn1_Salt.c are generated at compile
time in the heimdal sources by means of asn1_compile from lib/hdb/hdb.asn1.
Some definitions from the heimdal source upfront:

--- /usr/include/hdb_asn1.h: ---

typedef struct Key {
  unsigned int *mkvno;
  EncryptionKey key;
  Salt *salt;
} Key;

typedef struct Salt {  // heimdal-1.4
  unsigned int type;
  heim_octet_string salt;
} Salt;

typedef struct Salt {  // heimdal-1.5
  unsigned int type;
  heim_octet_string salt;
  heim_octet_string *opaque;	// New, must by initialized, otherwise this code segfaults in function length_Salt in asn1_Salt.c
} Salt;

typedef struct heim_octet_string {
  size_t length;
  void *data;
} heim_octet_string;

--- /usr/include/krb5_asn1.h: ---

typedef struct EncryptionKey {
  krb5int32 keytype;
  heim_octet_string keyvalue;
} EncryptionKey;

--- /usr/include/krb5.h: ---

typedef EncryptionKey krb5_keyblock;

typedef struct krb5_salt {
    krb5_salttype salttype;
    krb5_data saltvalue;
} krb5_salt;

typedef heim_octet_string krb5_data;

*/

PyObject* asn1_encode_key(PyObject *self, PyObject* args)
{
	krb5KeyblockObject *keyblock;
	krb5SaltObject *salt;
	int mkvno;
	krb5_error_code err;
	char *buf;
	size_t len;
	Key asn1_key = {0};
	Salt asn1_salt = {0};

	if (!PyArg_ParseTuple(args, "O!Oi", &krb5KeyblockType, &keyblock, &salt, &mkvno))
		return NULL;

	//asn1_key.mkvno = &mkvno;
	asn1_key.mkvno = NULL;

	// Embed keyblock->keyblock of type krb5_keyblock into asn1_key of type Key
	asn1_key.key = keyblock->keyblock;	// EncryptionKey := krb5_keyblock, now we have void *asn1_key.key.keyvalue.data == keyblock->keyblock.keyvalue.data

	if ((PyObject*)salt == Py_None) {
		asn1_key.salt = NULL;
	} else if (!PyObject_TypeCheck(salt, &krb5SaltType)) {
		PyErr_SetString(PyExc_TypeError, "argument 2 must be heimdal.krb5Salt or None");
		return NULL;
	} else {
		// First embed salt->salt of type krb5_salt into asn1_salt of type Salt
		asn1_salt.type = salt->salt.salttype;
		asn1_salt.salt = salt->salt.saltvalue;	// heim_octet_string := krb5_data, now we have void *asn1_salt.salt.data == *salt->salt.saltvalue.data

		// Then embed asn1_salt of type Salt into  asn1_key of type Key
		asn1_key.salt = &asn1_salt;
	}

	ASN1_MALLOC_ENCODE(Key, buf, len, &asn1_key, &len, err);
	if (err != 0) {
		Py_RETURN_NONE;
	} else {
		PyObject *s = PyString_FromStringAndSize(buf, len);
		free(buf);
		return s;
	}
}

PyObject* asn1_decode_key(PyObject *unused, PyObject* args)
{
	uint8_t *key_buf;
	Py_ssize_t key_len;
	krb5KeyblockObject *keyblock = NULL;
	krb5SaltObject *salt = NULL;
	krb5_error_code err;
	Key asn1_key;
	size_t len;
	PyObject *self = NULL;
	krb5ContextObject *context = NULL;

	if (!PyArg_ParseTuple(args, "s#|O!", &key_buf, &key_len, &krb5ContextType, &context))
		return NULL;

	if (context == NULL) {
		context = context_open(NULL);
		if (context == NULL) {
			PyErr_NoMemory();
			goto except;
		}
	} else {
		Py_INCREF(context);
	}

	err = decode_Key(key_buf, key_len, &asn1_key, &len);
	if (err) {
		krb5_exception(context->context, err);
		goto except;
	}

	keyblock = (krb5KeyblockObject *) PyObject_NEW(krb5KeyblockObject, &krb5KeyblockType);
	if (keyblock == NULL) {
		PyErr_NoMemory();
		goto except;
	}
	Py_INCREF(context);
	keyblock->context = context;
	keyblock->keyblock.keytype = asn1_key.key.keytype;
	keyblock->keyblock.keyvalue.data = malloc(asn1_key.key.keyvalue.length);
	if (keyblock->keyblock.keyvalue.data == NULL) {
		PyErr_NoMemory();
		goto except;
	}
	memcpy(keyblock->keyblock.keyvalue.data, asn1_key.key.keyvalue.data, asn1_key.key.keyvalue.length);
	keyblock->keyblock.keyvalue.length = asn1_key.key.keyvalue.length;

	salt = (krb5SaltObject *) PyObject_NEW(krb5SaltObject, &krb5SaltType);
	if (salt == NULL) {
		PyErr_NoMemory();
		goto except;
	}
	Py_INCREF(context);
	salt->context = context;
	if (asn1_key.salt != NULL) {
		salt->salt.salttype = asn1_key.salt->type;
		salt->salt.saltvalue.data = malloc(asn1_key.salt->salt.length);
		if (salt->salt.saltvalue.data == NULL) {
			PyErr_NoMemory();
			goto except;
		}
		memcpy(salt->salt.saltvalue.data, asn1_key.salt->salt.data, asn1_key.salt->salt.length);
		salt->salt.saltvalue.length = asn1_key.salt->salt.length;
	} else {
		/*
		Py_INCREF(Py_None);
		salt = Py_None;
		*/
		salt->salt.salttype = KRB5_PW_SALT;
		salt->salt.saltvalue.data   = NULL;
		salt->salt.saltvalue.length = 0;
	}
	self = Py_BuildValue("(OOi)", keyblock, salt, asn1_key.mkvno);
	goto finally;

except:
	if (keyblock) {
		free(keyblock->keyblock.keyvalue.data);
		keyblock->keyblock.keyvalue.data = NULL;
	}
	if (salt) {
		free(salt->salt.saltvalue.data);
		salt->salt.saltvalue.data = NULL;
	}
finally:
	Py_XDECREF(context);
	Py_XDECREF(keyblock);
	Py_XDECREF(salt);
	return self;
}
