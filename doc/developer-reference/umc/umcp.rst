.. _umc-umcp2:

Protocol UMCP 2.0
=================

This protocol is used by the UMC server for external clients and between the UMC
server and its UMC module processes.

.. warning::

   UMCP is deprecated and will be removed in the nearer future. The protocol
   elements are described here for completeness and not for use. Always use the
   HTTP interface instead!

.. _umc-umcp2-flow:

Data flow
---------

The protocol is based on a server/client model. The client sends requests to the
server that will be answered with a response message by the server.

With a status code in the response message the client can determine the type of
result of its request:

* An error occurred during the processing of the request. The status code
  contains details of the error.

* The command was processed successfully. A status message may contain details
  about the performed task.

.. _umc-umcp2-auth:

Authentication
--------------

Before a client may send request messages to the server that contain commands to
execute, the client has to authenticate. After a successful authentication the
UMC server determines the permissions for the user defined by policies in the
LDAP directory. If the LDAP server is not reachable a local cache is checked for
previously discovered permissions. If none of these sources is available the
user is prohibited to use any command.

The authentication process within the UMC server uses the PAM service
``univention-management-console``. By default, this service uses a cache for
credentials if the LDAP server is not available to provide the possibility to
access the UMC server also in case of problems with the LDAP server.

.. _umc-umcp2-message:

Message format
--------------

The messages, request and response, have the same format that consists
of a single header line, one empty line and the body.

The header line contains control information that allows the UMC server
to verify the correctness of the message without reading the rest of the
message.

.. _umc-umcp2-message-header:

Message header
~~~~~~~~~~~~~~

The header defines the message type, a unique identifier, the length of
the message body in bytes, the command and the mime type of the body.

``(REQUEST|RESPONSE)/<id>/<length of body>[/<mime-type>]: <command>[ <arguments>]``

By the first keyword the message type is defined. Supported message types are
``REQUEST`` and ``RESPONSE``. Any other type will be ignored.

Separated by a ``/`` the message id follows, that must be unique within a
communication channel. By default it consists of a timestamp and a counter.

The next field is a number, defining the length of the body in bytes, starting
to count after the empty line.

Since UMCP 2.0 there is as another field specifying the mime type of the body.
If not given then the guessed value for the mime type is ``application/json``.
If the body can't be decoded using a JSON parser the message is invalid.

The last two fields define the UMCP command that should be executed by the
server. The following commands are supported:

``AUTH``
   This commands sends an authentication request. It must be the first command
   send by the client. All commands send before a successful authentication are
   rejected.

``GET``
   This command is used to retrieve information from the UMC server, for example
   a list of all UMC modules available in this session.

``SET``
   This command is used to define settings for the session, for example the
   language.

``COMMAND``
   This command is used to pass requests to UMC modules. Each module defines a
   set of commands, that it implements. The UMC module command is defined by the
   first argument in the UMCP header, for example a request like
   ``REQUEST/123423423-01/42/application/json: COMMAND ucr/query`` passes on the
   module command ``ucr/query`` to a UMC module.

.. _umc-umcp2-message-body:

Message body
~~~~~~~~~~~~

The message body may contain one object of any type, for example an image, an
OpenOffice document or a JSON object. The JSON object is the default type and is
the only supported mime type for request messages. It contains a dictionary that
has a few predefined keys (for both message types):

``options``
   Contains the arguments for the command.

``status``
   Defines the status code in response messages. The codes are similar to the
   HTTP status codes, for example ``200`` defines a successful execution of the
   command.

``message``
   May contain a human readable description of the status code. This may contain
   details to explain the user the situation.

``flavor``
   An optional field. If given in a request message the module may act
   differently than without the flavor.

.. _umc-umcp2-example:

Examples
--------

This section contains a few example messages of UMCP 2.0.

.. code-block::
   :caption: Authentication request
   :name: umc-umcp2-example-auth

   REQUEST/130928961341733-1/147/application/json: AUTH

   {"username": "root", "password": "univention"}


Request:

.. code-block::
   :caption: Search for users
   :name: umc-umcp2-example-users

   REQUEST/130928961341726-0/125/application/json: COMMAND udm/query

   {"flavor": "users/user",
    "options": {"objectProperty": "name",
                "objectPropertyValue": "test1*1",
                "objectType": "users/user"}}


Response:

.. code-block::
   :caption: Response to the command request
   :name: umc-example-command-response

   RESPONSE/130928961341726-0/1639/application/json: COMMAND udm/query

   {"status": 200,
    "message": null,
    "options": {"objectProperty": "name",
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
