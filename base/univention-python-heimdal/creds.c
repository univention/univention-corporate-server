/*
 * Python Heimdal
 *	Bindings for the credentials API of heimdal
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

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "principal.h"
#include "creds.h"

static struct PyMethodDef creds_methods[];

static krb5_error_code kerb_prompter(krb5_context ctx, void *data,
	       const char *name, const char *banner, int num_prompts,
	       krb5_prompt prompts[])
{
	if (num_prompts == 0) return 0;

	memset(prompts[0].reply->data, 0, prompts[0].reply->length);
	if (prompts[0].reply->length > 0) {
		if (data) {
			strncpy(prompts[0].reply->data, data, prompts[0].reply->length-1);
			prompts[0].reply->length = strlen(prompts[0].reply->data);
		} else {
			prompts[0].reply->length = 0;
		}
	}
	return 0;
}

krb5CredsObject *creds_from_creds(krb5_context context, krb5_creds creds)
{
	krb5CredsObject *self = (krb5CredsObject *) PyObject_New(krb5CredsObject, &krb5CredsType);
	if (self == NULL)
		return NULL;

	self->context = context;
	self->creds = creds;

	return self;
}

krb5CredsObject *creds_new(PyObject *unused, PyObject *args)
{
	krb5_error_code ret;
	krb5ContextObject *context;
	krb5PrincipalObject *principal;
	char *password_string;
	char *in_tkt_service;
	if (!PyArg_ParseTuple(args, "OOss", &context, &principal, &password_string,
				&in_tkt_service))
		return NULL;

	krb5CredsObject *self = (krb5CredsObject *) PyObject_NEW(krb5CredsObject, &krb5CredsType);
	if (self == NULL)
		return NULL;

	/* FIXME */
	if (in_tkt_service[0] == '\0')
		in_tkt_service = NULL;

	self->context = context->context;

	ret = krb5_get_init_creds_password(self->context, &self->creds,
			principal->principal, NULL, kerb_prompter, password_string,
			0, in_tkt_service, NULL);
	if (ret) {
		Py_DECREF(self);
		krb5_exception(NULL, ret);
		return NULL;
	}

	return self;
}

/* FIXME */
PyObject *creds_parse(krb5CredsObject *self, PyObject *args)
{
	krb5_error_code ret;
	PyObject *tuple;
	Ticket t;
	size_t len;
	char *s;

	if ((tuple = PyTuple_New(3)) == NULL)
		return NULL;

	decode_Ticket(self->creds.ticket.data, self->creds.ticket.length, &t, &len);

	ret = krb5_enctype_to_string(self->context, t.enc_part.etype, &s);
	if (ret != 0) {
		if (asprintf(&s, "unknown (%d)", t.enc_part.etype) < 0) {
			Py_DECREF(tuple);
			return PyErr_NoMemory();
		}
	}
	PyTuple_SetItem(tuple, 0, PyString_FromString(s));
	free(s);

	if (t.enc_part.kvno)
		PyTuple_SetItem(tuple, 1, PyInt_FromLong(*t.enc_part.kvno));
	else
		PyTuple_SetItem(tuple, 1, PyInt_FromLong(-1));

	ret = krb5_unparse_name(self->context, self->creds.server, &s);
	if (ret) {
		krb5_exception(self->context, 1, ret, "krb5_unparse_name");
		Py_DECREF(tuple);
		return NULL;
	}
	PyTuple_SetItem(tuple, 2, PyString_FromString(s));
	free(s);

	//PyTuple_SetItem(tuple, 0, PyInt_FromLong(entry.vno));
	//PyTuple_SetItem(tuple, 1, PyString_FromString(etype));
	//PyTuple_SetItem(tuple, 2, PyString_FromString(principal));
	//PyTuple_SetItem(tuple, 3, PyInt_FromLong(entry.timestamp));
	//PyTuple_SetItem(tuple, 4, PyString_FromString(entry.keyblock.keyvalue.data));

	return tuple;
}

PyObject *creds_change_password(krb5CredsObject *self, PyObject *args)
{
	krb5_error_code ret;
	char *newpw;
	int result_code;
	krb5_data result_code_string;
	krb5_data result_string;

	if (!PyArg_ParseTuple(args, "s", &newpw))
		return NULL;

	// principal is set to NULL -> set_password uses the default principal in set case
	ret = krb5_set_password(self->context, &self->creds, newpw, NULL, &result_code,
			&result_code_string, &result_string);
	if (ret) {
		krb5_exception(NULL, ret);
		return NULL;
	}

	krb5_data_free(&result_code_string);
	krb5_data_free(&result_string);

	Py_RETURN_NONE;
}

void creds_destroy(krb5CredsObject *self)
{
	krb5_free_cred_contents(self->context, &self->creds);
	PyObject_Del(self);
}

static PyObject *creds_getattr(krb5CredsObject *self, char *name)
{
	return Py_FindMethod(creds_methods, (PyObject *)self, name);
}

PyTypeObject krb5CredsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Creds",			/*tp_name*/
	sizeof(krb5CredsObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)creds_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)creds_getattr,	/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef creds_methods[] = {
	{"parse", (PyCFunction)creds_parse, METH_VARARGS, "Parse creds to tuple"},
	{"change_password", (PyCFunction)creds_change_password, METH_VARARGS, "Change password"},
	{NULL, NULL, 0, NULL}
};
