/*
 * Python Heimdal
 *	Bindings for the realm object of heimdal
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

#include "error.h"
#include "context.h"
#include "realm.h"

#if 0
krb5RealmObject *realm_from_realm(krb5ContextObject *context, krb5_realm *realm)
{
	krb5RealmObject *self = (krb5RealmObject *) PyObject_New(krb5RealmObject, &krb5RealmType);
	if (self == NULL)
		return NULL;

	Py_INCREF(context);
	self->context = context;
	self->realm = realm;

	return self;
}
#endif

static void realm_dealloc(krb5RealmObject *self)
{
#if 0
	Py_DECREF(self->context);
#endif
	Py_TYPE(self)->tp_free(self);
}

static struct PyMethodDef realm_methods[] = {
	{NULL},
};

PyTypeObject krb5RealmType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Realm",
	.tp_doc = "Heimdal Kerberos realm",
	.tp_basicsize = sizeof(krb5RealmObject),
	/* methods */
	.tp_dealloc = (destructor)realm_dealloc,
	.tp_methods = realm_methods,
	.tp_flags = Py_TPFLAGS_DEFAULT,
};
