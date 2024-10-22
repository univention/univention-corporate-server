.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _udm-rest-api:

|UCSREST|
=========

UCS provides a |UCSREST| which can be used to inspect, modify, create and
delete UDM objects through HTTP requests.

The API is accessible from :samp:`https://{FQHN}/univention/udm/`.

.. seealso::

   For an architectural overview,
   see :external+uv-architecture:ref:`services-udm-rest-api`
   in :cite:t:`ucs-architecture`.

.. _udm-rest-api-authentication:

Authentication
--------------

To use the API you have to authenticate with a user account which is a member of
an authorized group. The group authorization is managed through the |UCSUCRVs|
:envvar:`directory/manager/rest/authorized-groups/<group-name>`.

You can authenticate through the following ways:

* With user credentials through :rfc:`HTTP basic authentication <7617>`

* An OAuth 2.0 Access Token as JWT through :rfc:`HTTP Bearer authentication <6750>`

The API comes predefined with the following UCR variables:

* :envvar:`directory/manager/rest/authorized-groups/domain-admins`
* :envvar:`directory/manager/rest/authorized-groups/dc-backup`
* :envvar:`directory/manager/rest/authorized-groups/dc-slaves`

The variables authorize the groups ``Domain Admins``, ``DC Backup Hosts`` and
``DC Slave Hosts`` respectively.

To authorize additional groups you just have to create a new UCR variable. If
you haven't already, create the group you want to authorize:

.. code-block:: console

   $ udm groups/group create \
     --position="cn=groups,$(ucr get ldap/base)" \
     --set name="UDM API Users"


Now set the UCR variable to allow the group members to use the API.

.. code-block:: console

   $ ucr set directory/manager/rest/authorized-groups/udm-api-users=\
   "cn=UDM API Users,cn=groups,$(ucr get ldap/base)"


.. note::

   The authorization of a group only allows the group members to access the API
   in the first place. After that, which actions the user can perform with the
   API is regulated through ACLs. For example a normal ``Domain Users`` user can't
   create or delete objects.

After you add or modify a |UCSUCRV|
:envvar:`directory/manager/rest/authorized-groups/<group-name>` you have to
restart the API service for the changes to take effect.

.. code-block:: console

   $ systemctl restart univention-directory-manager-rest


.. _udm-rest-api-overview:

API overview
------------

You can interact with the API by sending HTTP requests to resources and by using
different HTTP methods you can achieve different results.

.. list-table:: HTTP methods
   :header-rows: 1
   :widths: 3 9

   * - Verb
     - Description

   * - GET
     - Retrieve a resource

   * - POST
     - Create a resource

   * - PUT
     - Replace or move a resource

   * - PATCH
     - Modify or move a resource

   * - DELETE
     - Delete a resource

For an in depth overview over which resources are available, which HTTP methods
are allowed on them and which query parameters are available for a given HTTP
method visit :samp:`https://{FQHN}/univention/udm/schema/` with a browser.
To download the OpenAPI schema, use :samp:`https://{FQHN}/univention/udm/openapi.json`.
The contract is that the client must always use the latest schema.

You can navigate the OpenAPI schema interactively with a web browser.
To enable it, use the following steps:

#. You need to set the UCR variable
   :envvar:`directory/manager/rest/html-view-enabled` to ``true``.

#. If you need to insert JSON blobs of objects into the HTML source code,
   enable it by setting
   :envvar:`directory/manager/rest/debug-mode-enabled` to ``true``.

#. Restart the |UCSREST| with this command:

   .. code-block:: console

      $ systemctl restart univention-directory-manager-rest

#. Finally, visit :samp:`https://{FQHN}/univention/udm/`.

.. _udm-rest-api-clients:

API clients
-----------

The following API clients implemented in Python exist for the |UCSREST|:

* :program:`python3-univention-directory-mananger-rest-client`:

  Every UCS system has it installed by default.
  You can use it the following way:

  .. code-block:: python
     :caption: Example for using Python |UCSREST| client


     from univention.admin.rest.client import UDM
     from univention.config_registry import ucr

     uri = 'https://%(hostname)s.%(domainname)s/univention/udm/' % ucr
     udm = UDM.http(uri, 'Administrator', 'univention')
     module = udm.get('users/user')

     # 1. create a user
     obj = module.new()
     obj.properties['username'] = 'foo'
     obj.properties['password'] = 'univention'
     obj.properties['lastname'] = 'foo'
     obj.save()

     # 2. search for users (first user)
     obj = next(module.search('uid=*'))
     if obj:
         obj = obj.open()
     print('Object {}'.format(obj))

     # 3. get by dn
     ldap_base = udm.get_ldap_base()
     obj = module.get('uid=foo,cn=users,%s' % (ldap_base,))

     # 4. get referenced objects e.g. groups
     pg = obj.objects['primaryGroup'].open()
     print(pg.dn, pg.properties)
     print(obj.objects['groups'])

     # 5. modify
     obj.properties['description'] = 'foo'
     obj.save()

     # 6. move to the ldap base
     obj.move(ldap_base)

     # 7. remove
     obj.delete()

* :program:`python3-univention-directory-mananger-rest-async-client`:

  After installing the Debian package on a UCS system,
  you can use it in the following way:

  .. code-block:: python
     :caption: Example for using Python asynchronous UDM REST API client

     import asyncio
     from univention.admin.rest.async_client import UDM
     from univention.config_registry import ucr

     uri = 'https://%(hostname)s.%(domainname)s/univention/udm/' % ucr

     async def main():
         async with UDM.http(uri, 'Administrator', 'univention') as udm:
             module = await udm.get('users/user')

             # 1. create a user
             obj = await module.new()
             obj.properties['username'] = 'foo'
             obj.properties['password'] = 'univention'
             obj.properties['lastname'] = 'foo'
             await obj.save()

             # 2. search for users (first user)
             objs = module.search()
             async for obj in objs:
                 if not obj:
                     continue
                 obj = await obj.open()
                 print('Object {}'.format(obj))

             # 3. get by dn
             ldap_base = await udm.get_ldap_base()
             obj = await module.get('uid=foo,cn=users,%s' % (ldap_base,))

             # 4. get referenced objects e.g. groups
             pg = await obj.objects['primaryGroup'].open()
             print(pg.dn, pg.properties)
             print(obj.objects['groups'])

             # 5. modify
             obj.properties['description'] = 'foo'
             await obj.save()

             # 6. move to the ldap base
             await obj.move(ldap_base)

             # 7. remove
             await obj.delete()

* Python |UCSREST| Client:

  * `Package at PyPI <https://pypi.org/project/udm-rest-client/>`_
  * :external+python-udm-rest-client:doc:`Documentation <index>`


.. _udm-rest-api-usage-examples:

API usage examples
------------------

In the following section you will learn how to create, modify, search and delete
a user through the API.

While you try out these examples you will often see the *"_links"* and
*"_embedded"* properties in the responses. These properties are defined by *HAL*,
the *Hypertext Application Language*, which is used in the API. These properties
contain links which can be used to traverse the API. For example the *"_links"*
property of the response to a paginated query could contain the *"next"* property
which points to the next page.

For more information on *HAL* please refer to the `Internet Draft for HAL
<ietf-hal_>`_.

.. _udm-rest-api-usage-examples-post:

Create a user with a POST request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a new user your first want to get a template that describes a valid
user and has all attributes filled out with default values.

You can get the template for an UDM module with:

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/${module}/add


So for the users/user module you get the template with:

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add


To work with the template, you can save it into a file. To make it
more readable, you can use something like Pythons
:py:mod:`json.tool`.

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add | \
     python3 -m json.tool > user_template.json


The JSON file contains meta information (keys that start with underscore
'``_``') that aren't necessary to create a user. These can be filtered out to
make it easier to work with the template file. The following example produces
such a condensed template:

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add | \
     python3 -c 'import sys, json; \
       template = json.load(sys.stdin); \
       template = {key:value for key, value in template.items() if not key.startswith("_")}; \
       json.dump(template, sys.stdout, indent=4)' > user_template.json


The content of :file:`user_template.json` should look something like this.

.. code-block:: js

   {
       "position": "cn=users,dc=mydomain,dc=intranet",
       "objectType": "users/user",
       "options": {
           "pki": false
       },
       "policies": {
           "policies/pwhistory": [],
           "policies/umc": [],
           "policies/desktop": []
       },
       "properties": {
           "mobileTelephoneNumber": [],
           "certificateSubjectOrganisationalUnit": null,
           "groups": [],
           "sambahome": null,
           "departmentNumber": [],
           "certificateSerial": null,
           "certificateSubjectCommonName": null,
           "primaryGroup": "cn=Domain Users,cn=groups,dc=mydomain,dc=intranet",
           "uidNumber": null,
           "disabled": false,
           "unlock": false,
           "street": null,
           "postcode": null,
           "scriptpath": null,
           "sambaPrivileges": [],
           "description": null,
           "certificateIssuerCommonName": null,
           "mailForwardCopyToSelf": false,
           "employeeType": null,
           "homedrive": null,
           "overridePWLength": null,
           "title": null,
           "mailAlternativeAddress": [],
           "userCertificate": null,
           "organisation": null,
           "homeSharePath": "",
           "certificateIssuerOrganisationalUnit": null,
           "e-mail": [],
           "userexpiry": null,
           "pwdChangeNextLogin": false,
           "mailHomeServer": null,
           "unixhome": "/home/",
           "gecos": "",
           "sambaUserWorkstations": [],
           "preferredLanguage": null,
           "certificateIssuerState": null,
           "pagerTelephoneNumber": [],
           "username": null,
           "umcProperty": [],
           "certificateIssuerCountry": null,
           "homeTelephoneNumber": [],
           "shell": "/bin/bash",
           "homePostalAddress": [],
           "firstname": null,
           "certificateIssuerOrganisation": null,
           "lastname": null,
           "city": null,
           "certificateSubjectMail": null,
           "mailForwardAddress": [],
           "phone": [],
           "gidNumber": null,
           "birthday": null,
           "employeeNumber": null,
           "objectFlag": [],
           "sambaLogonHours": null,
           "certificateSubjectLocation": null,
           "displayName": "",
           "password": null,
           "lockedTime": null,
           "sambaRID": null,
           "secretary": [],
           "certificateSubjectOrganisation": null,
           "overridePWHistory": null,
           "mailPrimaryAddress": null,
           "country": null,
           "roomNumber": [],
           "certificateSubjectCountry": null,
           "locked": false,
           "certificateDateNotBefore": null,
           "passwordexpiry": null,
           "certificateVersion": null,
           "homeShare": null,
           "certificateIssuerMail": null,
           "unlockTime": null,
           "serviceprovider": [],
           "profilepath": null,
           "certificateIssuerLocation": null,
           "jpegPhoto": null,
           "certificateDateNotAfter": null,
           "certificateSubjectState": null
       }
   }


Now you can modify the attributes the new user should have and send the modified
template, through a :command:`POST` request, to create a new user.

.. code-block:: console

   $ curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/ --data @user_template.json


.. _udm-rest-api-usage-examples-get:

Search for users with a GET request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example you search for a users/user object where the property
``firstname`` starts with ``"Ale"`` and the property ``lastname`` ends with
``"er"``.

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
     "http://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/?query\[firstname\]=Al%2A&query\[lastname\]=%2Aer"


The response should look something like this (some fields where omitted for
clarity):

.. code-block:: js

   {
       "_embedded": {
           "udm:object": [
               {
                   "dn": "uid=alexpower,cn=users,dc=mydomain,dc=intranet",
                   "id": "alexpower",
                   "objectType": "users/user",
                   "options": {
                       "pki": false
                   },
                   "policies": {
                       "policies/desktop": [],
                       "policies/pwhistory": [],
                       "policies/umc": []
                   },
                   "position": "cn=users,dc=mydomain,dc=intranet",
                   "properties": {
                       "birthday": null,
                       "city": null,
                       "country": null,
                       "departmentNumber": [],
                       "description": null,
                       "disabled": false,
                       "displayName": "Alex Power",
                       "e-mail": [],
                       "employeeNumber": null,
                       "employeeType": null,
                       "firstname": "Alex",
                       "gecos": "Alex Power",
                       "gidNumber": 5001,
                       "groups": [
                           "cn=Domain Users,cn=groups,dc=mydomain,dc=intranet"
                       ],
                       "homePostalAddress": [],
                       "homeShare": null,
                       "homeSharePath": "alexpower",
                       "homeTelephoneNumber": [],
                       "homedrive": null,
                       "jpegPhoto": null,
                       "lastname": "Power",
                       "locked": false,
                       "lockedTime": "0",
                       "mailAlternativeAddress": [],
                       "mailForwardAddress": [],
                       "mailForwardCopyToSelf": "0",
                       "mailHomeServer": null,
                       "mailPrimaryAddress": null,
                       "mobileTelephoneNumber": [],
                       "objectFlag": [],
                       "organisation": null,
                       "overridePWHistory": null,
                       "overridePWLength": null,
                       "pagerTelephoneNumber": [],
                       "password": null,
                       "passwordexpiry": null,
                       "phone": [],
                       "postcode": null,
                       "preferredLanguage": null,
                       "primaryGroup": "cn=Domain Users,cn=groups,dc=mydomain,dc=intranet",
                       "profilepath": null,
                       "pwdChangeNextLogin": false,
                       "roomNumber": [],
                       "sambaLogonHours": null,
                       "sambaPrivileges": [],
                       "sambaRID": 5018,
                       "sambaUserWorkstations": [],
                       "sambahome": null,
                       "scriptpath": null,
                       "secretary": [],
                       "serviceprovider": [],
                       "shell": "/bin/bash",
                       "street": null,
                       "title": null,
                       "uidNumber": 2009,
                       "umcProperty": {},
                       "unixhome": "/home/alexpower",
                       "unlock": false,
                       "unlockTime": "",
                       "userexpiry": null,
                       "username": "alexpower"
                   },
                   "uri": "http://10.200.28.110/univention/udm/users/user/uid%3Dalexpower%2Ccn%3Dusers%2Cdc%3Dmydomain%2Cdc%3Dintranet"
               }
           ]
       },
       "results": 1
   }


.. _udm-rest-api-usage-examples-put:

Modify a user with a PUT request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To modify a user you first get the current state of the user. To prevent
modification conflicts you also have to get the entity tag (*Etag*) of the user
resource. The *Etag* can be found in the response headers; it is used to identify
a specific version of a resource.

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" --dump-header user.headers \
     https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn> \
     | python3 -m json.tool > user.json


.. caution::

   You must URL encode ``<dn>``.

Now you can edit the user in the :file:`user.json` file to your liking. After
you are done, send the changed :file:`user.json` through a :command:`PUT`
request to modify the user. To avoid modification conflicts it is required to
send the value of the *Etag* header, which you saved earlier in the
:file:`user.headers` file, as the value for the ``If-Match`` header.

.. code-block:: console

   $ curl -X PUT -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -H 'If-Match: "<Etag>"' \
     "https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn>" --data @user.json


.. caution::

   You must URL encode ``<dn>``.

   The quotes around the *Etag* are required.

.. _udm-rest-api-usage-examples-delete:

Delete a user with a DELETE request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete a user you just have to send a :command:`DELETE` request to
:samp:`/univention/udm/users/user/{<dn>}`. Optionally, you can provide
an ``If-Match`` header, similar to the :command:`PUT` method described
above, to ensure the deletion is conditional.

.. code-block:: console

   $ curl -X DELETE -H "Accept: application/json" \
     -H 'If-Match: "<Etag>" \
     'https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn>


.. caution::

   You must URL encode ``<dn>``.

.. _udm-rest-api-error-codes:

API Error Codes
---------------

The |UCSREST| can respond to requests with the following error codes. The list is not exhaustive:

.. list-table:: |UCSREST| error codes
   :header-rows: 1
   :widths: 1 3 8

   * - Code
     - Name
     - Example Case

   * - 400
     - Bad Request
     - The API doesn't understand the format of the request.

   * - 401
     - Unauthorized
     - The request provide no or wrong credentials for authorization.

   * - 403
     - Forbidden
     - User isn't part of the allowed groups to access the requested resource.

   * - 404
     - Not Found
     - The requested resource doesn't exist.

   * - 406
     - Not Acceptable
     - The header field ``Accept`` does not specify a known MIME media type
       or header field ``Accept-Language`` does not specify a known language.

   * - 412
     - Precondition Failed
     - The header ``If-Match`` does not match the E-tag or
       the header ``If-Unmodified-Since`` doesn't match the
       header ``Last-Modified``.

   * - 413
     - Payload Too Large
     - The request payload contains a field that exceeds its size limit.

   * - 416
     - Range Not Satisfiable
     - In the request, the field ``If-Match`` doesn't match the entity tag and
       the request has the field ``Range`` set.

   * - 422
     - Unprocessable Content
     - The validation of input parameters failed.

   * - 500
     - Internal Server Error
     - Generic error code for internal server errors.

   * - 503
     - Service Unavailable
     - The server for the service isn't available, for example the LDAP server.

.. spelling:word-list::

   Unprocessable
