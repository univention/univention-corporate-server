.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _fed-auth-verification:

Verify the configuration of federated authentication
====================================================

After completing the configuration,
you can verify that federated authentication works correctly
by signing in to the *Management UI* with an administrator account from the upstream IAM.

.. _fed-auth-test-login:

Test the sign-in
----------------

#. Open the *Management UI* login page.

#. Select **Single Sign-On (OIDC)**.

#. Select **Or sign in with** and choose the upstream identity provider.

#. Sign in with a user account from the upstream IAM.

#. After successful sign-in,
   The *Management UI* opens and the available management modules are visible.

Depending on the assigned guardian roles, you can search,
create, or modify UDM objects.

.. _fed-auth-test-logging:

Logging
-------

The UMC server logs every successful sign-in by a federated user.

Review the log file :file:`/var/log/univention/management-console-server.log`.
For an example log entry, see :numref:`fed-auth-log-message`.
This message confirms that:

* the user signed in successfully
* the upstream IAM provided the identifier, which Nubus recognized
* Nubus applied the guardian roles to the session

.. code-block:: console
   :caption: Example UMC log message for federated sign-in
   :name: fed-auth-log-message

   2026-03-07T07:58:57.007719+00:00 PROCESS \
     OIDC login federated user '4f0fdab5-2979-4b25-87b7-5ecdf623547e' with \
     roles ['udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou1,dc=ucs,dc=test'] \
     pid=348275 logname=MAIN func=oidc.handle_federated_account:191 umcmodule=server requester_ip=10.205.2.83

