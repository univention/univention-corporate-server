==============
UMC web server
==============

With the new generation of UMC there is also an HTTP server available
that can be used to access the UMC server. The web server is implemented
as a frontend to the UMC server and translates HTTP requests to
UMCP commands.

--------
Examples
--------

The output is re-wrapped for readability.

Authentication request
======================

::

	POST URL:http://10.200.15.31/univention/auth HTTP/1.1

::

	{"options":{"username":"root","password":"univention"}}

Request: search for users
=========================

::

	POST URL:http://10.200.15.31/univention/command/udm/query HTTP/1.1

::

	{"options": {
	  "container":"all",
	  "objectType":"users/user",
	  "objectProperty":"username",
	  "objectPropertyValue":"test1*1"},
	 "flavor":"users/user"}

Response: search for users (body)
=================================

::

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
