.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _chap-provisioning:

********************
Provisioning Service
********************

.. index::
   single: provisioning service
   single: Provisioning API

The *Provisioning Service* is an event messaging service
that notifies subscribed services about changes in the LDAP directory.
When data changes in the LDAP directory on the :external+uv-ucs-operation:term:`Primary Directory Node`,
the *Provisioning Service* receives a notification
and forwards it to all subscribed services.
In contrast to the |UCSUDL|,
the *Provisioning Service* provides the |UCSUDM| representation of changed objects
instead of their LDAP representation.

Applications and apps from the *App Center* can subscribe to events for topics,
such as specific UDM object types,
for example ``users/user`` or ``groups/group``.
The *Provisioning Service* creates a queue for each app
and stores incoming events there.
The app can fetch and acknowledge events from its queue at its own pace,
rather than relying on LDAP polling
or the :external+uv-app-center:ref:`file-based listener mechanism <provisioning-push>` in UCS.

.. _provisioning-api-client:

Manage subscriptions through CLI commands
=========================================

.. index::
   single: provisioning service; univention-provisioning-api-client

.. versionadded:: 5.2-6

UCS provides the command-line tool :file:`/usr/sbin/univention-provisioning-api-client`.
The tool manages subscriptions with the *Provisioning API*.
Run the tool on a UCS host
that has the *Provisioning API* installed
and access to the required credential files.
You can run it manually or automatically,
for example from join scripts for apps.

The tool uses two distinct sets of credentials:

Administrator credentials
   You can find the administrator credentials in :file:`/etc/provisioning-secrets.json`
   under the key ``PROVISIONING_API_ADMIN_PASSWORD``.
   The *Provisioning Service* requires them only to register and remove subscriptions.
   This file is available only on the UCS host
   that has the *Provisioning API* installed.
   The file isn't available inside Docker containers.
   For security reasons, don't make the file available to containers.
   The administrator credentials use the format shown in
   :numref:`provisioning-api-client-administrator-credentials-format-listing`.

   .. code-block:: json
      :caption: Format of the administrator credentials file
      :name: provisioning-api-client-administrator-credentials-format-listing

      {
        "PROVISIONING_API_ADMIN_PASSWORD": "<password>"
      }

.. _provisioning-api-client-subscription-credentials:

Subscription credentials
   When you use the CLI tool with the ``subscribe`` sub-command,
   the tool creates a name and a random password
   and writes them to the subscription file.
   The container uses the subscription credentials
   to authenticate with the *Provisioning API* and consume events.
   The subscription credentials use the format shown in
   :numref:`provisioning-api-client-subscription-credentials-format-listing`.

   .. code-block:: json
      :caption: Format of the subscription credentials file.
      :name: provisioning-api-client-subscription-credentials-format-listing

      {
        "subscription_name": "sub-<uuid>",
        "subscription_password": "<password>"
      }

Docker-based UCS apps manage subscriptions in the join script,
the :file:`inst` file that runs directly on the UCS host.
You need to store the subscription file in the app's data directory
so the container can read the subscription credentials at runtime.

.. _provisioning-api-client-subscribe:

Subscribe to topics in the Provisioning Service
===============================================

.. program:: univention-provisioning-api-client subscribe

The ``subscribe`` sub-command registers a subscription with the *Provisioning API*.
If the subscription file already exists and contains valid credentials,
the sub-command uses those credentials.
Otherwise, the tool generates new credentials, saves them to the file,
and registers the subscription.

:numref:`provisioning-subscribe-example` shows how to subscribe
to the *Provisioning Service*.

This section provides a reference for the ``subscribe`` sub-command.

.. code-block:: bash
   :caption: Subscribe to UDM ``users/user`` events in a join script
   :name: provisioning-subscribe-example

   /usr/sbin/univention-provisioning-api-client subscribe \
       --topics '[{"realm": "udm", "topic": "users/user"}]' \
       --subscription-file "/var/lib/univention-appcenter/apps/${APP_ID}/data/provisioning-subscription.json"

.. option:: --topics <json>

   :option:`--topics` is a required parameter.
   It's a JSON array of realm and topic pairs
   that specify which events the subscription wants to receive.
   Each entry must be a JSON object with a ``realm`` key and a ``topic`` key.
   The realm ``"udm"`` covers all |UCSUDM| object types;
   the topic matches the UDM module name,
   for example ``"users/user"`` or ``"groups/group"``.

   The following example shows a value:
   ``'[{"realm": "udm", "topic": "users/user"}, {"realm": "udm", "topic": "groups/group"}]'``

.. option:: --subscription-file <path>

   :option:`--subscription-file` is a required parameter.
   It provides the path to the file with the :ref:`provisioning-api-client-subscription-credentials`.
   The tool creates the file if it doesn't exist yet.
   It uses the credentials,
   if the file exists and contains valid credentials,
   for example to update an existing subscription.

   The tool writes the file with the file mode bits ``0600``
   and uses the format in :numref:`provisioning-api-client-subscription-credentials-format-listing`.

   You need to store the subscription credentials file in the app's data directory,
   for example :file:`/var/lib/univention-appcenter/apps/{appid}/data/`,
   so the containerized app can read the credentials to consume events.

.. option:: --subscription-name <name>

   Defines a unique name for the subscription within the *Provisioning API* server
   to identify the subscription.
   If you omit this parameter, the tool reads the name from the subscription file.
   If the file doesn't exist yet,
   the tool automatically generates a name in the format ``sub-<uuid>``.

.. option:: --force

   The :option:`--force` lets the tool overwrite an existing subscription.
   It deletes and recreates the subscription.
   Without the :option:`--force` parameter,
   the command exits with an error
   if a subscription with the same name already exists on the server.

.. option:: --request-prefill

   The :option:`--request-prefill` parameter requests the tool
   to pre-fill the subscription queue with the current state of all matching objects at registration time.
   Use this option when the app needs the full current dataset on first startup,
   not only changes going forward.
   Overwriting a subscription with ``--request-prefill`` set triggers a new prefill.

.. option:: --admin-credential-file <path>

   The :option:`--admin-credential-file` provides the path
   to the file with the :ref:`provisioning-api-client-administrator-credentials` for the *Provisioning API*.
   It defaults to :file:`/etc/provisioning-secrets.json`.
   The file in the default path only exists
   if the *Provisioning API* is available on the system.

   For the format and the required content of the administrator credentials file,
   see :ref:`provisioning-api-client-administrator-credentials`.

.. option:: --provisioning-server <fqdn>

   If you don't want to use the local system,
   or if the automatically assigned fully qualified domain name (FQDN) is incorrect,
   specify the FQDN of the *Provisioning API* server.
   If the *Provisioning API* server isn't the local system,
   you must provide its administrator credentials using :option:`--admin-credential-file`.
   The default is the FQDN of the local host.

.. _provisioning-api-client-unsubscribe:

Unsubscribe from the Provisioning Service
=========================================

.. program:: univention-provisioning-api-client unsubscribe

The ``unsubscribe`` sub-command removes an existing subscription from the *Provisioning API*.
It reads the subscription credentials from the subscription file
and uses the administrator credentials to delete the subscription.
It doesn't remove the subscription file.
Use this action in the unjoin script,
as shown in :numref:`provisioning-unsubscribe-example`.
The *App Center* then calls it when it removes the app.

.. code-block:: bash
   :caption: Unsubscribe in an unjoin script
   :name: provisioning-unsubscribe-example

   /usr/sbin/univention-provisioning-api-client unsubscribe \
       --subscription-file "/var/lib/univention-appcenter/apps/${APP_ID}/data/provisioning-subscription.json"

.. option:: --subscription-file <path>

   :option:`--subscription-file` is a required parameter.
   It provides the path to the subscription credentials file created during ``subscribe``.
   The tool reads the subscription name and password from this file.
   The command exits with an error if the file doesn't exist.

.. option:: --admin-credential-file <path>

   The :option:`--admin-credential-file` provides the path
   to the file with the :ref:`provisioning-api-client-administrator-credentials` for the *Provisioning API*.
   The default path is :file:`/etc/provisioning-secrets.json`.

.. option:: --provisioning-server <fqdn>

   If you don't want to use the local system,
   or if the automatically assigned fully qualified domain name (FQDN) is incorrect,
   specify the FQDN of the *Provisioning API* server.
   If the *Provisioning API* server isn't the local system,
   you must provide its :ref:`provisioning-api-client-administrator-credentials` using :option:`--admin-credential-file`.
   The default is the FQDN of the local host.

.. _provisioning-join-script:

Use the tool in join and unjoin scripts
=======================================

.. program:: univention-provisioning-api-client subscribe

Use the :command:`univention-provisioning-api-client` tool
to register the subscription in the join script
and remove it in the unjoin script.
Set :option:`--subscription-file` to a path inside the app's data directory
so that the containerized app can read the credentials and consume events.
Use :option:`--force` so that re-running the join script during an app update
overwrites the existing subscription rather than failing.

.. important::

   If you overwrite a subscription with :option:`--request-prefill`,
   the tool triggers a new prefill of the subscription.

For a join script fragment example, see :numref:`provisioning-join-example`.
For an unjoin script fragment example, see :numref:`provisioning-unjoin-example`.

.. code-block:: bash
   :caption: Join script fragment — register a *Provisioning Service* subscription
   :name: provisioning-join-example

   APP_ID="myapp"
   SUBSCRIPTION_FILE="/var/lib/univention-appcenter/apps/${APP_ID}/data/provisioning-subscription.json"

   /usr/sbin/univention-provisioning-api-client subscribe \
       --topics '[{"realm": "udm", "topic": "users/user"}]' \
       --subscription-file "$SUBSCRIPTION_FILE" \
       --force \
       --request-prefill \
       --provisioning-server "$(hostname -f)" || die

.. code-block:: bash
   :caption: Unjoin script fragment — remove the Provisioning Service subscription
   :name: provisioning-unjoin-example

   APP_ID="myapp"
   SUBSCRIPTION_FILE="/var/lib/univention-appcenter/apps/${APP_ID}/data/provisioning-subscription.json"

   if [ -f "$SUBSCRIPTION_FILE" ]; then
       /usr/sbin/univention-provisioning-api-client unsubscribe \
           --subscription-file "$SUBSCRIPTION_FILE" || die
   fi

.. spelling::

   prefill
