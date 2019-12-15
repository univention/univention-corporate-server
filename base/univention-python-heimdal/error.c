/*
 * Python Heimdal
 *	Bindings for the error handling API of heimdal
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
#include <krb5_err.h>

#if PY_MAJOR_VERSION >= 3
#define PyInt_FromLong PyLong_FromLong
#endif

static PyObject *Krb5_exception_class;

static PyObject *error_objects;

PyObject *krb5_exception(krb5_context context, int code, ...)
{
	PyObject *errobj;

	if (code == ENOENT) {
		PyErr_SetNone(PyExc_IOError);
	} else {
		PyObject *i = PyInt_FromLong(code);
		errobj = PyDict_GetItem(error_objects, i);
		Py_DECREF(i);
		if (errobj == NULL)
			errobj = Krb5_exception_class;
		if (context) {
			const char *msg = krb5_get_error_message(context, code);
			PyErr_Format(errobj, "%s (%d)", msg, code);
			krb5_free_error_message(context, msg);
		} else {
			PyErr_SetNone(errobj);
		}
	}

	return NULL;
}

void error_init(PyObject *self)
{
	PyObject *dict = PyDict_New();
	PyDict_SetItemString(dict, "code", Py_None);
	Krb5_exception_class = PyErr_NewException("heimdal.Krb5Error", NULL, dict);
	Py_DECREF(dict);
	PyDict_SetItemString(self, "Krb5Error", Krb5_exception_class);

	error_objects = PyDict_New();

#	define seterrobj(n) { \
		PyObject *i = PyInt_FromLong(n);			\
		PyObject *d = PyDict_New();				\
		PyDict_SetItemString(d, "code", i);	\
		PyObject *e = PyErr_NewException("heimdal."#n, Krb5_exception_class, d);		\
		Py_DECREF(d);						\
		PyDict_SetItem(error_objects, i, e);			\
		Py_DECREF(i);						\
		PyDict_SetItemString(self, #n, e);			\
		Py_DECREF(e);						\
	}

#if 1
#include "error_gen.c"
#endif
}
