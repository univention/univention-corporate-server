/*
 * Python Heimdal
 *	Bindings for the ASN.1 API of heimdal
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

#include <Python.h>
#include <krb5_asn1.h>
#include <hdb_asn1.h>

#include "keyblock.h"
#include "salt.h"

PyObject* asn1_encode_key(PyObject *self, PyObject* args)
{
	krb5KeyblockObject *keyblock;
	krb5SaltObject *salt;
	int mkvno;
	krb5_error_code ret;
	unsigned char *buf;
	size_t len;
	Key asn1_key;
	Salt asn1_salt;

	if (!PyArg_ParseTuple(args, "OOi", &keyblock, &salt, &mkvno))
		return NULL;

	//asn1_key.mkvno = &mkvno;
	asn1_key.mkvno = NULL;
	asn1_key.key = keyblock->keyblock;
	if ((PyObject*)salt != Py_None) {
		asn1_salt.type = salt->salt.salttype;
		asn1_salt.salt = salt->salt.saltvalue;
		asn1_key.salt = &asn1_salt;
	} else {
		asn1_key.salt = NULL;
	}

	ASN1_MALLOC_ENCODE(Key, buf, len, &asn1_key, &len, ret);
	if (ret != 0) {
		Py_INCREF(Py_None);
		return Py_None;
	} else {
		PyObject *s = PyString_FromStringAndSize(buf, len);
		Py_INCREF(s); /* FIXME */
		return s;
	}
}
