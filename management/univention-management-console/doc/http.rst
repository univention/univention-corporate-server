.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

==============
HTTP Interface
==============

With the new generation of UMC there is also an HTTP server available.

--------
Examples
--------

The output is re-wrapped for readability.

Authentication request
======================

.. code-block:: http

   POST https://example.org/univention/auth HTTP/1.1

.. code-block:: json

   {"options": {"username": "root", "password": "univention"}}

Request: search for users
=========================

.. code-block:: http

   POST https://example.org/univention/command/udm/query HTTP/1.1

.. code-block:: json

   {"options": {
     "container":"all",
     "objectType":"users/user",
     "objectProperty":"username",
     "objectPropertyValue":"test1*1"},
    "flavor":"users/user"}

Response: search for users (body)
=================================

.. code-block:: json

   {"status": 200,
    "message": null,
    "options": {
     "objectProperty": "username",
     "container": "all",
     "objectPropertyValue": "test1*1",
     "objectType": "users/user"},
    "result": [
     {"ldap-dn": "uid=test11,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test11",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test101,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test101",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test111,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test111",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test121,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test121",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test131,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test131",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test141,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test141",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test151,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test151",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test161,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test161",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test171,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test171",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test181,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test181",
      "objectType": "users/user"},
     {"ldap-dn": "uid=test191,cn=users,dc=univention,dc=qa",
      "path": "univention.qa:/users",
      "name": "test191",
      "objectType": "users/user"}]}
