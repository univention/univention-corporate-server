/*
 * Python Heimdal
 *	Bindings for the keytab object of heimdal
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
 *
 * Heimdal:
 * Copyright (c) 1997 - 2001 Kungliga Tekniska Högskolan
 * (Royal Institute of Technology, Stockholm, Sweden).
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#include <Python.h>

#include "error.h"
#include "keytab.h"
#include "context.h"

krb5KeytabObject *keytab_open(PyObject *unused, PyObject *args)
{
	char *keytab_string;
	krb5_error_code ret;
	char keytab_buf[256];
	krb5ContextObject *context;
	if (!PyArg_ParseTuple(args, "Os", &context, &keytab_string))
		return NULL;

	krb5KeytabObject *self = (krb5KeytabObject *) PyObject_New(krb5KeytabObject, &krb5KeytabType);
	if (self == NULL)
		return NULL;

	if ((self->context = malloc(sizeof(krb5_context))) == NULL) {
		Py_DECREF(self);
		PyErr_NoMemory();
		return NULL;
	}
	if ((self->keytab = malloc(sizeof(krb5_keytab))) == NULL) {
		free(self->context);
		Py_DECREF(self);
		PyErr_NoMemory();
		return NULL;
	}
	*self->context = context->context;

	ret = krb5_init_context(self->context);
	if (ret)
		errx (1, "krb5_init_context failed: %d", ret);

	if (keytab_string == NULL) {
		ret = krb5_kt_default_name (*self->context, keytab_buf, sizeof(keytab_buf));
		if (ret) {
			krb5_warn(*self->context, ret, "krb5_kt_default_name");
			free(self->keytab);
			free(self->context);
			Py_DECREF(self);
			return NULL;
		}
		keytab_string = keytab_buf;
	}

	ret = krb5_kt_resolve(*self->context, keytab_string, self->keytab);
	if (ret) {
		krb5_warn(*self->context, ret, "resolving keytab %s", keytab_string);
		free(self->keytab);
		free(self->context);
		Py_DECREF(self);
		return NULL;
	}

	return self;
}

static void keytab_destroy(krb5KeytabObject *self)
{
	if (self->keytab) {
		krb5_kt_close(*self->context, *self->keytab);
		free(self->keytab);
	}
	if (self->context) {
		free(self->context);
	}

	PyObject_Del(self);
}

static PyObject *keytab_add(krb5KeytabObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5_keytab_entry entry;
	char *principal_string = NULL;
	int kvno = -1;
	char *enctype_string = NULL;
	krb5_enctype enctype;
	char *password_string = NULL;
	int salt_flag = 1;
	int random_flag = 0;

	if (!PyArg_ParseTuple(args, "sissii", &principal_string, &kvno,
				&enctype_string, &password_string,
				&salt_flag, &random_flag))
		return NULL;

	memset(&entry, 0, sizeof(entry));

	ret = krb5_parse_name(*self->context, principal_string, &entry.principal);
	if(ret) {
		krb5_exception(*self->context, ret, "%s", principal_string);
		goto out;
	}

	ret = krb5_string_to_enctype(*self->context, enctype_string, &enctype);
	if(ret) {
		int t;
		if(sscanf(enctype_string, "%d", &t) == 1)
			enctype = t;
		else {
			krb5_exception(*self->context, ret, "%s", enctype_string);
			goto out;
		}
	}

	if(password_string) {
		if (!salt_flag) {
			krb5_salt salt;
			krb5_data pw;

			salt.salttype         = KRB5_PW_SALT;
			salt.saltvalue.data   = NULL;
			salt.saltvalue.length = 0;
			pw.data = (void*)password_string;
			pw.length = strlen(password_string);
			krb5_string_to_key_data_salt(*self->context, enctype, pw, salt,
					&entry.keyblock);
		} else {
			krb5_string_to_key(*self->context, enctype, password_string,
					entry.principal, &entry.keyblock);
		}
	} else {
		krb5_generate_random_keyblock(*self->context, enctype, &entry.keyblock);
	}

	entry.vno = kvno;
	entry.timestamp = time (NULL);
	ret = krb5_kt_add_entry(*self->context, *self->keytab, &entry);
	if(ret) {
		krb5_exception(*self->context, ret, "add");
		goto out;
	}

 out:
	krb5_kt_free_entry(*self->context, &entry);

	Py_RETURN_NONE;
}

static PyObject *keytab_list(krb5KeytabObject *self, PyObject *args)
{
	krb5_error_code ret;
	krb5_keytab_entry entry;
	krb5_kt_cursor cursor;
	PyObject *list = NULL;

	ret = krb5_kt_start_seq_get(*self->context, *self->keytab, &cursor);
	if(ret) {
		krb5_exception(*self->context, ret, "krb5_kt_start_seq_get");
		return NULL;
	}

	if ((list = PyList_New(0)) == NULL) {
		krb5_kt_end_seq_get(*self->context, *self->keytab, &cursor);
		return PyErr_NoMemory();
	}

	while((ret = krb5_kt_next_entry(*self->context, *self->keytab, &entry, &cursor)) == 0){
		char *etype, *principal;
		PyObject *tuple;

		if ((tuple = PyTuple_New(5)) == NULL) {
			krb5_kt_free_entry(*self->context, &entry);
			Py_DECREF(list);
			return PyErr_NoMemory();
		};

		PyTuple_SetItem(tuple, 0, PyInt_FromLong(entry.vno));

		ret = krb5_enctype_to_string(*self->context,
						 entry.keyblock.keytype, &etype);
		if (ret != 0) {
			if (asprintf(&etype, "unknown (%d)", entry.keyblock.keytype) < 0) {
				krb5_kt_free_entry(*self->context, &entry);
				Py_DECREF(tuple);
				Py_DECREF(list);
				return PyErr_NoMemory();
			}
		}

		PyTuple_SetItem(tuple, 1, PyString_FromString(etype));
		//PyTuple_SetItem(tuple, 1, PyInt_FromLong(entry.keyblock.keytype));

		krb5_unparse_name(*self->context, entry.principal, &principal);
		PyTuple_SetItem(tuple, 2, PyString_FromString(principal));

		PyTuple_SetItem(tuple, 3, PyInt_FromLong(entry.timestamp));

		//if(list_keys) {
		//	int i;
		//	kp->key = malloc(2 * entry.keyblock.keyvalue.length + 1);
		//	for(i = 0; i < entry.keyblock.keyvalue.length; i++)
		//	snprintf(kp->key + 2 * i, 3, "%02x",
		//		 ((unsigned char*)entry.keyblock.keyvalue.data)[i]);
		//	CHECK_MAX(key);
		//}
		PyTuple_SetItem(tuple, 4, PyString_FromStringAndSize(entry.keyblock.keyvalue.data, entry.keyblock.keyvalue.length));

		PyList_Append(list, tuple);
		krb5_kt_free_entry(*self->context, &entry);
	}
	krb5_kt_end_seq_get(*self->context, *self->keytab, &cursor);

	return list;
}

static PyObject *keytab_remove(krb5KeytabObject *self, PyObject *args)
{
	krb5_error_code ret = 0;
	krb5_keytab_entry entry;
	char *principal_string = NULL;
	krb5_principal principal = NULL;
	int kvno = 0;
	char *keytype_string = NULL;
	krb5_enctype enctype = 0;

	if (!PyArg_ParseTuple(args, "sis", &principal_string, &kvno,
				&keytype_string))
		return NULL;

	if (principal_string) {
		ret = krb5_parse_name(*self->context, principal_string, &principal);
		if (ret) {
			krb5_exception(*self->context, ret, "%s", principal_string);
			return NULL;
		}
	}
	if (keytype_string) {
		ret = krb5_string_to_enctype(*self->context, keytype_string, &enctype);
		if (ret) {
			int t;
			if(sscanf(keytype_string, "%d", &t) == 1)
				enctype = t;
			else {
				krb5_exception(*self->context, ret, "%s", keytype_string);
				goto out;
			}
		}
	}
	if (!principal && !enctype && !kvno) {
		krb5_warnx(*self->context,
			   "You must give at least one of "
			   "principal, enctype or kvno.");
		goto out;
	}

	entry.principal = principal;
	entry.keyblock.keytype = enctype;
	entry.vno = kvno;
	ret = krb5_kt_remove_entry(*self->context, *self->keytab, &entry);

	if(ret) {
		krb5_exception(*self->context, ret);
		goto out;
	}
	Py_RETURN_NONE;

 out:
	if(principal)
		krb5_free_principal(*self->context, principal);

	return NULL;
}

static struct PyMethodDef keytab_methods[] = {
	{"add", (PyCFunction)keytab_add, METH_VARARGS, "Add principal to keytab"},
	{"list", (PyCFunction)keytab_list, METH_VARARGS, "List keytab"},
	{"remove", (PyCFunction)keytab_remove, METH_VARARGS, "Remove principal from keytab"},
	{NULL}
};

PyTypeObject krb5KeytabType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.Keytab",
	.tp_basicsize = sizeof(krb5KeytabObject),
	/* methods */
	.tp_dealloc = (destructor)keytab_destroy,
	.tp_methods = keytab_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
