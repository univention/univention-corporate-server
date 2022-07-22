.. _umc-http:
.. _umc-http-example:

Protocol HTTP for UMC
=====================

With the new generation of UMC there is also an HTTP server available that can
be used to access the UMC server. The web server is implemented as a front end to
the UMC server and translates HTTP POST requests to UMCP commands.

.. code-block::
   :caption: Authentication request
   :name: umc-http-example-auth

   POST http://192.0.2.31/univention/auth HTTP/1.1

   {"options": {"username": "root", "password": "univention"}}


Request:

.. code-block::
   :caption: Search for users
   :name: umc-http-example-user

   POST http://192.0.2.31/univention/command/udm/query HTTP/1.1

   {"options": {"container": "all",
               "objectType":"users/user",
               "objectProperty":"username",
               "objectPropertyValue":"test1*1"},
    "flavor":"users/user"}


Response:

.. code-block:: javascript
   :caption: Response
   :name: umc-http-example-response

   {"status": 200,
    "message": null,
    "options": {"objectProperty": "username",
                "container": "all",
                "objectPropertyValue": "test1*1",
                "objectType": "users/user"},
    "result": [{"ldap-dn": "uid=test11,cn=users,dc=univention,dc=qa",
                "path": "univention.qa:/users",
                "name": "test11",
                "objectType": "users/user"},
   ...
               {"ldap-dn": "uid=test191,cn=users,dc=univention,dc=qa",
                "path": "univention.qa:/users",
                "name": "test191",
                "objectType": "users/user"}]}
