
.. _udm-rest-api:

UDM REST API
============

UCS provides a REST API which can be used to inspect, modify, create and
delete UDM objects through HTTP requests.

The API is accessible from :samp:`https://{FQHN}/univention/udm/`.

.. _udm-rest-api-authentication:

Authentication
--------------

To use the API you have to authenticate with a user account which is a member of
an authorized group. The group authorization is managed through the |UCSUCRV|\ s
:envvar:`directory/manager/rest/authorized-groups/<group-name>`.

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
   > --position="cn=groups,$(ucr get ldap/base)" \
   > --set name="UDM API Users"


Now set the UCR variable to allow the group members to use the API.

.. code-block:: console

   $ ucr set directory/manager/rest/authorized-groups/udm-api-users= \
   > "cn=UDM API Users,cn=groups,$(ucr get ldap/base)"


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

By visiting :samp:`https://{FQHN}/univention/udm/` with a browser you can
navigate and use the API interactively.

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
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/${module}/add


So for the users/user module you get the template with:

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add


To work with the template, you can save it into a file. To make it
more readable, you can use something like Pythons
:py:mod:`json.tool`.

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add |
   > python -m json.tool > user_template.json


The JSON file contains meta information (keys that start with underscore
'``_``') that aren't necessary to create a user. These can be filtered out to
make it easier to work with the template file. The following example produces
such a condensed template:

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/add |
   > python -c 'import sys, json; \
   >   template = json.load(sys.stdin); \
   >   template = {key:value for key, value in template.items() if not key.startswith("_")}; \
   >   json.dump(template, sys.stdout, indent=4)' > user_template.json


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
           "pwdChangeNextLogin": null,
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
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/ --data @user_template.json


.. _udm-rest-api-usage-examples-get:

Search for users with a GET request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example you search for a users/user object where the property
``firstname`` starts with ``"Ale"`` and the property ``lastname`` ends with
``"er"``.

.. code-block:: console

   $ curl -X GET -H "Accept: application/json" \
   > "http://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/?query\[firstname\]=Al%2A&query\[lastname\]=%2Aer"


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
                       "pwdChangeNextLogin": null,
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
   > https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn> \
   > | python -m json.tool > user.json


.. caution::

   You must URL encode ``<dn>``.

Now you can edit the user in the :file:`user.json` file to your liking. After
you are done, send the changed :file:`user.json` through a :command:`PUT`
request to modify the user. To avoid modification conflicts it is required to
send the value of the *Etag* header, which you saved earlier in the
:file:`user.headers` file, as the value for the ``If-Match`` header.

.. code-block:: console

   $ curl -X PUT -H "Accept: application/json" -H "Content-Type: application/json" -H 'If-Match: "<Etag>"' \
   > "https://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn>" --data @user.json


.. caution::

   You must URL encode ``<dn>``.

   The quotes around the *Etag* are required.

.. _udm-rest-api-usage-examples-delete:

Delete a user with a DELETE request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete a user you just have to send a :command:`DELETE` request to
:samp:`/univention/udm/users/user/{<dn>}`

.. code-block:: console

   $ curl -X DELETE http://${USER}:${PASSWORD}@${FQHN}/univention/udm/users/user/<dn>


.. caution::

   You must URL encode ``<dn>``.
