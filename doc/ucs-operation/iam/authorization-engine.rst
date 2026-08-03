.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam-authorization-engine:

Authorization engine
====================

*Guardian* is the authorization engine in Nubus for UCS.
This page explains how to install, configure, and operate it.

This page covers:

* :ref:`iam-authorization-engine-endpoints`
* :ref:`iam-authorization-engine-system-roles`
* :ref:`iam-authorization-engine-install`
* :ref:`iam-authorization-engine-configure`
* :ref:`iam-authorization-engine-verify-return-decisions`
* :ref:`iam-authorization-engine-policies`
* :ref:`iam-authorization-engine-troubleshooting`

.. seealso::

   For reference documentation about the decision engine,
   see `Cerbos documentation <https://docs.cerbos.dev/cerbos/latest/index.html>`_.

.. _iam-authorization-engine-endpoints:

Authorization engine endpoints
------------------------------

The engine uses these ``localhost`` ports:

* An HTTP interface on port ``3592``.
* A gRPC interface on port ``3593``.

Services on the same system use these ports.
Containers on the system reach the engine
through the shared ``guardian`` Docker network,
under the hostname ``cerbos``.

.. warning::

   The engine accepts every request from the local system.
   It has no transport authentication.
   Install it only on Nubus for UCS systems where you trust all local services.

.. _iam-authorization-engine-system-roles:

Supported system roles for the authorization engine
---------------------------------------------------

Install the authorization engine on a :term:`Primary Directory Node`
or a :term:`Backup Directory Node`.
The *Univention App Center* offers it only on these roles.
A :term:`Replica Directory Node` and a :term:`Managed Node`
can't run it.

The following applies:

Local access only
   Install the engine next to the service that needs decisions.
   The engine answers local callers only.
   A service on another system can't reach it.
   Install the engine on each Nubus for UCS system
   whose services ask for decisions.

Independent installations
   Each installation operates independently.
   Each engine keeps its own copy of the policies
   and answers from that copy.
   The engines share no state and don't forward requests to each other.
   The listener module synchronizes the policy copies
   because every Nubus for UCS system reads the same policy bundles from the LDAP directory.

.. warning::

   The :program:`univention-guardian-server` package doesn't check the system role.
   Install the *Univention Guardian* app through the *App Center*.
   The App Center restricts the authorization engine to Primary and Backup Directory Nodes.
   Direct package installation bypasses this restriction.
   It can install the authorization engine and *Directory Listener* integration
   on an unsupported system role.

.. _iam-authorization-engine-install:

Install the authorization engine
--------------------------------

You need domain administrator permissions and a root account on the target system
to install the authorization engine.
For information about the domain administrator account,
see :external+uv-nubus-manual:ref:`nubus-authentication-sign-in-choose-user-account`
in :cite:t:`uv-nubus-manual`.

Install the *Univention Guardian* app from the *App Center*,
or run the command in :numref:`iam-authorization-engine-install-listing`.
For information about installing apps through the App Center,
see :ref:`lifecycle-app-center`.

.. code-block:: console
   :caption: Install the authorization engine
   :name: iam-authorization-engine-install-listing

   $ univention-app install univention-guardian

The installation makes the following changes to the system:

* It installs the :program:`univention-guardian-server` package.

* It creates the ``guardian-server`` system user
  and group with the fixed ID ``64110``.
  :program:`Cerbos` runs under this account.

* It installs the :program:`systemd` service
  ``univention-guardian-server.service``.
  The service runs :program:`Cerbos` as a container
  and starts the container after installation.
  If the container exits, :program:`systemd` restarts it.

* It installs the ``cerbos-policies`` listener module.
  The module installs policy bundles from the LDAP directory.
  For more information,
  see :ref:`iam-authorization-engine-policies`.

To verify that the service is active,
run the command in :numref:`iam-authorization-engine-status-listing`.
The output must show ``active (running)``.
If it doesn't,
see :ref:`iam-authorization-engine-troubleshooting`.

.. code-block:: console
   :caption: Show the state of the authorization engine
   :name: iam-authorization-engine-status-listing

   $ systemctl status univention-guardian-server.service

.. _iam-authorization-engine-verify:

Verify that the engine returns decisions
----------------------------------------

The default installation contains no policies,
but you can verify that the engine returns a decision.
The request in :numref:`iam-authorization-engine-verify-return-decisions`
asks whether the actor may read a resource of the application ``myapp``.
Without a matching policy,
the engine returns ``EFFECT_DENY``,
as shown in :numref:`iam-authorization-engine-verify-response-listing`.

.. code-block:: bash
   :caption: Verify that the engine returns decisions
   :name: iam-authorization-engine-verify-return-decisions

   $ curl -sS http://127.0.0.1:3592/api/check/resources \
       -H 'Content-Type: application/json' \
       -d '{
     "requestId": "r1",
     "principal": {"id": "alice", "roles": ["guardian:myapp-admin"]},
     "resources": [{
       "resource": {"id": "x", "kind": "guardian.management_api",
                    "attr": {"app_name": "myapp"}},
       "actions": ["read_resource"]
     }]
   }'

.. code-block:: json
   :caption: Expected decision from the authorization engine
   :name: iam-authorization-engine-verify-response-listing

   {
     "results": [
       {
         "actions": {
           "read_resource": "EFFECT_DENY"
         }
       }
     ]
   }

.. _iam-authorization-engine-configure:

Configure the authorization engine
----------------------------------

The :program:`univention-guardian-server` package manages these
:term:`UCR variables <UCR variable>`:

* :envvar:`guardian/cerbos/log-level`
* :envvar:`guardian/cerbos/audit-logging/enabled`

Changing either variable restarts the authorization engine.
Requests fail while the service restarts.

To diagnose a policy evaluation,
do the following as root:

#. Run the command in
   :numref:`iam-authorization-engine-enable-diagnostics-listing`
   to set the log level and enable audit logging.
   If you stop the diagnosis or can't complete it,
   immediately run the command in
   :numref:`iam-authorization-engine-reset-diagnostics-listing`
   to reset the variables to their default values.

   .. code-block:: console
      :caption: Enable diagnostic logging for policy evaluation
      :name: iam-authorization-engine-enable-diagnostics-listing

      $ ucr set \
        guardian/cerbos/log-level=DEBUG \
        guardian/cerbos/audit-logging/enabled=true

#. Reproduce the policy evaluation that you want to diagnose.

#. Read the service log with the command in
   :numref:`iam-authorization-engine-log-listing`.

#. Run the command in
   :numref:`iam-authorization-engine-reset-diagnostics-listing`
   to reset the variables to their default values.

   .. code-block:: console
      :caption: Reset diagnostic logging for policy evaluation
      :name: iam-authorization-engine-reset-diagnostics-listing

      $ ucr set \
        guardian/cerbos/log-level=WARN \
        guardian/cerbos/audit-logging/enabled=false

#. Run the command in
   :numref:`iam-authorization-engine-verify-diagnostics-listing`
   to verify the default values.

   .. code-block:: console
      :caption: Verify diagnostic logging defaults
      :name: iam-authorization-engine-verify-diagnostics-listing

      $ ucr get guardian/cerbos/log-level
      WARN
      $ ucr get guardian/cerbos/audit-logging/enabled
      false

.. caution::

   Debug and audit logs contain request payloads,
   which can include personal data.
   Enable these settings only for as long as you need them.

The remaining settings of the engine are static.
Nubus for UCS generates the files
:file:`/usr/share/univention-guardian-server/docker-compose.yaml` and
:file:`/usr/share/univention-guardian-server/config/cerbos.yaml`
from UCR templates.
Don't edit these files.
A UCR update overwrites your changes.

.. seealso::

   :ref:`system-administration-ucr`
      for information about local system configuration with UCR.

.. _iam-authorization-engine-policies:

Manage the policies of the authorization engine
-----------------------------------------------

A policy defines the actions that an actor can perform on a resource.
The engine loads every policy file in
:file:`/usr/share/univention-guardian-server/policies/`
and its subdirectories.
Each subdirectory holds the policies of one source.

An application or a package registers its policies
as a *policy bundle* in the LDAP directory.
The listener module ``cerbos-policies`` installs each bundle
into the subdirectory :samp:`policies/{APPLICATION}/`
on every Nubus for UCS system that runs the engine.
The module validates each bundle before applying it.
If the bundle doesn't compile,
the module keeps the previous policies and discards the bundle.

To list the policy files in the local policy directory,
run the command in :numref:`iam-authorization-engine-policies-listing`.

.. code-block:: console
   :caption: List the policy files in the local policy directory
   :name: iam-authorization-engine-policies-listing

   $ ls -R /usr/share/univention-guardian-server/policies/

The engine doesn't reload policies while it runs.
Every policy change requires a service restart.
After the listener module installs a policy bundle,
it automatically restarts the service.
If you copy a policy file to the Nubus for UCS system yourself,
restart the authorization engine service with the command in
:numref:`iam-authorization-engine-restart-listing`.

.. code-block:: console
   :caption: Restart the authorization engine
   :name: iam-authorization-engine-restart-listing

   $ systemctl restart univention-guardian-server.service

.. note::

   Copy a policy file to a Nubus for UCS system only for local testing.
   The next package update removes the file,
   and no other authorization engine in the domain receives it.

.. seealso::

   `Cerbos | Policies <https://docs.cerbos.dev/cerbos/latest/policies/>`_
      for information about the policy format.

.. _iam-authorization-engine-troubleshooting:

Diagnose the authorization engine
---------------------------------

This section describes the authorization engine logs
and common causes of problems.

To see which policies the engine loaded
and why it skipped a policy,
read the log of the service with the command in
:numref:`iam-authorization-engine-log-listing`.

.. code-block:: console
   :caption: Read the log of the authorization engine
   :name: iam-authorization-engine-log-listing

   $ journalctl -u univention-guardian-server.service

Check the listener log with the command in
:numref:`iam-authorization-engine-listener-log-listing`.
It shows whether the listener module installed or rejected a policy bundle.

.. code-block:: console
   :caption: Read the listener log for policy bundles
   :name: iam-authorization-engine-listener-log-listing

   $ grep cerbos-policies /var/log/univention/listener.log

The following list describes common symptoms and their causes:

The engine denies an action that a policy allows.
   The engine bases its decision on the request content.
   Enable :envvar:`guardian/cerbos/audit-logging/enabled`
   and compare the logged request with the condition in the policy.
   In most cases, the calling service didn't send an expected attribute
   or role.

A policy change has no effect.
   The engine doesn't reload policies while it runs.
   Restart the service as shown in :numref:`iam-authorization-engine-restart-listing`.
   If you registered a policy bundle,
   read the listener log.
   The module rejects a bundle that doesn't compile.

The engine ignores a policy file.
   :program:`Cerbos` treats a file whose name ends in ``_test.yaml`` as a test file,
   not as a policy.
   Rename the file.

A request fails with a connection error.
   The :program:`Cerbos` service restarts when you change a UCR variable
   and when the listener module applies a policy bundle.
   Requests fail during the restart.
   The calling service retries failed requests.

The engine doesn't start.
   The authorization engine :program:`Cerbos` runs as a container.
   Read the log of the service.
   Verify that ``docker.service`` runs.
