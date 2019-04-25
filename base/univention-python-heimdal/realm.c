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

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "realm.h"

krb5RealmObject *realm_from_realm(krb5_context context, krb5_realm *realm)
{
	krb5RealmObject *self = (krb5RealmObject *) PyObject_New(krb5RealmObject, &krb5RealmType);
	if (self == NULL)
		return NULL;

	self->context = context;
	self->realm = realm;

	return self;
}

void realm_destroy(krb5RealmObject *self)
{
	PyObject_Del(self);
}

PyTypeObject krb5RealmType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"krb5Realm",			/*tp_name*/
	sizeof(krb5RealmObject),	/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)realm_destroy,	/*tp_dealloc*/
	0,				/*tp_print*/
	0,				/*tp_getattr*/
	0,				/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};

static struct PyMethodDef realm_methods[] = {
	{NULL},
};
