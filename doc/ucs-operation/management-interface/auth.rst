.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _ucs-operation-auth:

**************
Authentication
**************

This page covers configuration aspects around authentication in Nubus for UCS
for technical administrators.
For a general description,
see :external+uv-nubus-manual:ref:`nubus-authentication`
in :cite:t:`uv-nubus-manual`.

.. _ucs-operation-auth-sign-in:

Sign-in
=======

For a general description of sign-in,
see :external+uv-nubus-manual:ref:`nubus-authentication-sign-in`
in :cite:t:`uv-nubus-manual`.
This section covers settings and peculiarities for Nubus for UCS.

.. _ucs-operation-auth-sign-in-choose-account:

Choose the right user account
-----------------------------

To sign in, enter the *Username* and *Password* of the corresponding domain account in the login mask.

.. _ucs-operation-auth-sign-in-choose-account-admin:

``Administrator``
   For the general description,
   see :external+uv-nubus-manual:ref:`nubus-authentication-sign-in-choose-user-account-administrator`
   in :cite:t:`uv-nubus-manual`.
   For a specific description of Nubus for UCS, continue reading.

   When you sign in
   on a :term:`UCS Primary Directory Node` or :term:`UCS Backup Directory Node`,
   the *Management UI* shows the management modules
   for the administration and configuration of the local system
   as well as the modules for the administration of data in the domain.

   .. TODO: Add reference to the installation wizard during setup, when the section becomes available.

   You specified the initial password for the ``Administrator`` account
   in the setup wizard during installation.
   The password corresponds to the initial password of the local ``root`` account.
   Use the ``Administrator`` account for the initial sign-in
   at a newly installed :term:`UCS Primary Directory Node`.

.. _ucs-operation-auth-sign-in-choose-account-root:

``root``
   In some cases, it might be necessary to sign in with the system's local ``root`` account.
   For more information, refer to :external+uv-ucs-manual:ref:`computers-rootaccount`.
   The ``root`` account only enables access to UMC modules for the administration and configuration of the local system.

   .. TODO: Replace reference to the UCS Manual, as soon as the referred section becomes available.

.. _ucs-operation-auth-sign-in-choose-account-others:

Other user accounts
   For the general description,
   see :external+uv-nubus-manual:ref:`nubus-authentication-sign-in-choose-user-account-others`
   in :cite:t:`uv-nubus-manual`.

.. _ucs-operation-auth-sign-in-session-timeout:

Change Nubus web session timeout
--------------------------------

You can change the timeout of the Nubus web session
through the UCR variable :envvar:`umc/http/session/timeout`.

.. _nubus-authentication-sign-out-refresh-tabs:

Refresh browser tabs on sign-out
================================

For a general description of sign-out,
see :external+uv-nubus-manual:ref:`nubus-authentication-sign-out`
in :cite:t:`uv-nubus-manual`.

After detecting a sign-out,
Nubus automatically refreshes all browser tabs
with an active *Portal* session.

You can prevent Nubus from reloading the browser tabs upon sign-out.
Set the UCR variable
:envvar:`portal/reload-tabs-on-logout`
to the value ``true``.
The default value is ``false``.

.. _ucs-operation-auth-sso:

Single sign-on
==============

For a general description of single sign-on,
see :external+uv-nubus-manual:ref:`nubus-authentication-sso`
in :cite:t:`uv-nubus-manual`.

.. _ucs-operation-auth-sso-saml:

SAML configuration for single sign-on
-------------------------------------

UCS supports single sign-on through SAML using the :program:`Keycloak` app.
Refer to
:external+uv-keycloak-app:ref:`login-portal`
in :cite:t:`ucs-keycloak-doc`.

.. _ucs-operation-auth-sso-saml-activate:

Activate SAML for single sign-on
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After completing the configuration for *Keycloak*,
use the following steps for a better user experience:

#. Ensure that all users in your domain
   who want to use the *Portal* and the *Management UI* with single sign-on
   can reach :samp:`ucs-sso-ng.{[Domain Name]}`.

#. Change the UCR variable :envvar:`portal/auth-mode` to ``saml``
   with the command in
   :numref:`ucs-operation-auth-sso-saml-listing`.

   .. code-block:: console
      :caption: Set *Portal* authentication mode to SAML
      :name: ucs-operation-auth-sso-saml-listing

      $ ucr set portal/auth-mode="saml"

#. To apply the configuration, restart the *Portal server* on every UCS node with the command in
   :numref:`ucs-operation-auth-sso-saml-restart-listing`.

   .. code-block:: console
      :caption: Restart *Portal* service
      :name: ucs-operation-auth-sso-saml-restart-listing

      $ systemctl restart univention-portal-server.service

.. _ucs-operation-auth-sso-saml-update-portal:

Update the default login tile in the Portal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restarting the *Portal server* automatically updates the *Login* link in the user menu.
However, you need to manually update the portal tile for the *Login* to use SAML.
The default portal has a preconfigured but deactivated single sign-on login tile.
Use the portal edit mode to enable it.

To replace the *Login* tile with the single sign-on tile,
follow these steps:

#. In the *Management UI*, open the *Portal* management module through
   :menuselection:`Domain --> Portal`.

#. To activate the preconfigured sign-in tile for SAML,
   edit the entry ``login-saml``,
   scroll down to the section *Advanced*,
   and activate the checkbox :guilabel:`Activated`.

#. To deactivate the default sign-in tile,
   edit the entry ``login-ucs``,
   scroll down to the section *Advanced*,
   and deactivate the checkbox :guilabel:`Activated`.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal`
      in :cite:t:`uv-nubus-manual`
      for information about the concept and the management of the *Portal* in Nubus.

.. _ucs-operation-auth-sso-saml-restore:

Restore login without single sign-on
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To change back to the default sign-in in UCS without single sign-on,
use the following steps:

#. Revert the steps in :ref:`ucs-operation-auth-sso-saml-update-portal`.

#. Set the UCR variable :envvar:`portal/auth-mode`
   to the value ``ucs``
   in :ref:`ucs-operation-auth-sso-saml-activate`.

.. _ucs-operation-auth-sso-oidc:

OpenID Connect for single sign-on
---------------------------------

OpenID Connect (OIDC) is a protocol that allows single sign-on.
OIDC is a more lightweight protocol than SAML.
It's one variant for using single sign-on in the *Portal* and the UCS management system.
This section describes how to use it with UCS.

Before you can use OIDC for single sign-on, you must meet the following requirements:

#. You must at least have :uv:erratum:`5.0x1118` installed throughout your UCS domain.

   For information about how to upgrade, refer to :ref:`software-ucs-updates`.

#. You must have the :program:`Keycloak` app installed in your UCS domain.

   For information about the installation of :program:`Keycloak`,
   refer to :external+uv-keycloak-app:ref:`app-installation`
   in :cite:t:`ucs-keycloak-doc`.

.. _ucs-operation-auth-sso-oidc-activate:

Activate OpenID Connect for single sign-on
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, you need to decide on which UCS systems you want to enable single sign-on using OpenID Connect.
Second, you need to apply the following steps to each of those UCS systems.

#. Deactivate SAML for *Portal* sign-in through the UCR variable :envvar:`umc/web/sso/enabled`
   so that the automatic sign-in doesn't try SAML first, but instead uses OIDC directly.

   Change the UCR variable :envvar:`umc/web/oidc/enabled` to ``true`` with the command in
   :numref:`ucs-operation-auth-sso-oidc-activate-listing`.

   .. code-block:: console
      :caption: Activate OpenID Connect and deactivate SAML
      :name: ucs-operation-auth-sso-oidc-activate-listing

      $ ucr set \
         umc/web/sso/enabled=false \
         umc/web/oidc/enabled=true

#. Run the join script for the UMC web server with the command in
   :numref:`ucs-operation-auth-sso-oidc-activate-join-script-listing`.

   .. code-block:: console
      :caption: Run join script for the UMC web server
      :name: ucs-operation-auth-sso-oidc-activate-join-script-listing

      $ univention-run-join-scripts \
         --force \
         --run-scripts \
         92univention-management-console-web-server.inst

#. Change the UCR variable :envvar:`portal/auth-mode` to ``oidc``
   with the command in
   :numref:`ucs-operation-auth-sso-oidc-portal-listing`.
   The default value is ``ucs``.

   .. code-block:: console
      :caption: Set *Portal* authentication mode to OIDC
      :name: ucs-operation-auth-sso-oidc-portal-listing

      $ ucr set portal/auth-mode="oidc"

#. To apply the configuration, restart the *Portal Server*
   on every UCS node with the command in
   :numref:`ucs-operation-auth-sso-saml-restart-listing`.

.. _ucs-operation-auth-sso-oidc-sign-in-links:

Create sign-in links
~~~~~~~~~~~~~~~~~~~~

Restarting the *Portal Server* automatically updates the *Login* link in the user menu.
You can optionally create a portal tile for the sign-in with OpenID Connect on
the :term:`UCS Primary Directory Node` with the commands in
:numref:`central-management-umc-login-single-sign-on-oidc-sign-in-links-listing`.

.. code-block:: console
   :caption: Create portal tile for sign-in with OpenID Connect
   :name: central-management-umc-login-single-sign-on-oidc-sign-in-links-listing

   $ udm portals/entry create --ignore_exists \
       --position "cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" \
       --set name=login-oidc \
       --append displayName="\"en_US\" \"Login (Single sign-on)\"" \
       --append displayName="\"de_DE\" \"Anmelden (Single Sign-on)\"" \
       --append description="\"en_US\" \"Log in to the portal\"" \
       --append description="\"de_DE\" \"Am Portal anmelden\"" \
       --append link='"en_US" "/univention/oidc/?location=/univention/portal/"' \
       --set anonymous=TRUE \
       --set activated=TRUE \
       --set linkTarget=samewindow \
       --set icon="$(base64 /usr/share/univention-portal/login.svg)"

   $ udm portals/category modify --ignore_exists \
       --dn "cn=domain-service,cn=category,cn=portals,cn=univention,$(ucr get ldap/base)"\
       --append entries="cn=login-oidc,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)"

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal`
      in :cite:t:`uv-nubus-manual`
      for information about the concept and the management of the *Portal* in Nubus.

.. _ucs-operation-auth-sso-oidc-verification:

Verification and log files
~~~~~~~~~~~~~~~~~~~~~~~~~~

To verify that the setup works,
open the URL :samp:`https://{FQDN}/univention/oidc/` in a web browser, such as Mozilla Firefox,
and sign in.
Open a management module, such as
:external+uv-nubus-manual:ref:`nubus-user-management-users`,
and perform a search.

You can find relevant logging information in the following locations on the UCS system:

* Log file: :file:`/var/log/univention/management-console.server.log`

* :program:`journald`: :command:`journalctl -u slapd.service`

To reflect the changes for the login method in the *Portal*,
you need to edit the *Login* tile manually,
similar to the setup described in :ref:`ucs-operation-auth-sso-saml`.
The link must point to ``/univention/oidc/``.

.. _ucs-operation-auth-sso-oidc-deactivate:

Deactivate OpenID Connect for single sign-on
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, you need to decide on which Nubus for UCS node
you want to deactivate single sign-on using OpenID Connect.
Second, you need to apply the following steps to each of those nodes.

#. Unset the UCR variable :envvar:`umc/web/oidc/enabled` with the command in
   :numref:`ucs-operation-auth-sso-oidc-deactivate-unset-oidc-listing`.

   .. code-block:: console
      :caption: Unset ``umc/web/oidc/enabled``
      :name: ucs-operation-auth-sso-oidc-deactivate-unset-oidc-listing

      $ ucr unset umc/web/oidc/enabled

#. Remove the :external+uv-keycloak-app:term:`OIDC RP` from Keycloak with the command in
   :numref:`ucs-operation-auth-sso-oidc-deactivate-remove-rp-listing`.

   .. code-block:: console
      :caption: Remove the OIDC RP from Keycloak
      :name: ucs-operation-auth-sso-oidc-deactivate-remove-rp-listing

      $ univention-keycloak oidc/rp remove \
         "$(ucr get umc/oidc/$(hostname -f)/client-id)"

#. Unset all UCR variables that you find using the commands in
   :numref:`ucs-operation-auth-sso-oidc-deactivate-search-ucr-listing`.

   .. code-block:: console
      :caption: Search for UCR variables to unset
      :name: ucs-operation-auth-sso-oidc-deactivate-search-ucr-listing

      $ ucr search --brief --key ^umc/oidc
      $ ucr search --brief --key ^ldap/server/sasl/oauthbearer

#. Remove the OIDC secret from the system and restart affected services
   with the commands in
   :numref:`ucs-operation-auth-sso-oidc-deactivate-remove-secret-listing`.

   .. code-block:: console
      :caption: Remove OIDC secret
      :name: ucs-operation-auth-sso-oidc-deactivate-remove-secret-listing

      $ rm -f \
         /etc/umc-oidc.secret \
         /usr/share/univention-management-console/oidc/http*
      $ systemctl restart slapd univention-management-console-server

#. Manually update the portal tile for *Login*,
   so that the link points to ``/univention/login/``.

#. Change the UCR variable :envvar:`portal/auth-mode` to ``ucs``
   and restart the *Portal Server*.
   For details, see :ref:`ucs-operation-auth-sso-saml-restore`.

.. _ucs-operation-auth-sso-oidc-non-standard-fqdn:

Identity provider with non-standard FQDN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default,
the FQDN for the :program:`Keycloak` identity provider is :samp:`ucs-sso-ng.{$domainname}`.
However, you can configure a different FQDN for the identity provider.
For more information,
see :external+uv-keycloak-app:ref:`use-case-custom-fqdn-idp` in :cite:t:`ucs-keycloak-doc`.

If you have such a setup,
you have to configure the identity provider
for the OpenID Connect authentication in UMC on each UCS system.
Change the UCR variable :envvar:`umc/oidc/issuer` to the FQDN of your :program:`Keycloak` identity provider
and run the join script of the UMC web server again,
as shown in
:numref:`ucs-operation-auth-sso-oidc-non-standard-fqdn-listing`.

.. code-block:: console
   :caption: Set non-standard FQDN for identity provider :program:`Keycloak`
   :name: ucs-operation-auth-sso-oidc-non-standard-fqdn-listing

   $ IDP="auth.extern.test"
   $ ucr set umc/oidc/issuer="https://$IDP/realms/ucs"
   $ univention-run-join-scripts --force \
      --run-scripts 92univention-management-console-web-server

.. _ucs-operation-auth-sso-oidc-non-standard-fqdn-portal:

Non-standard FQDN for the Univention Portal and Management UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the *Management UI* is available under the FQDN
:samp:`{$hostname}.{$domainname}`.
If you have a setup with a different FQDN for the *Management UI*,
you have to change the UCR variable
:envvar:`umc/oidc/rp/server`
to the FQDN of the *Management UI*,
and run the join script of the UMC web server again,
as shown in :numref:`ucs-operation-auth-sso-oidc-non-standard-fqdn-portal-listing`.

.. code-block:: console
   :caption: Set non-standard FQDN for the *Portal* and *Management UI*
   :name: ucs-operation-auth-sso-oidc-non-standard-fqdn-portal-listing

   $ ucr set umc/oidc/rp/server="portal.extern.test"
   $ univention-run-join-scripts --force \
      --run-scripts 92univention-management-console-web-server
   $ systemctl restart slapd

.. important::

   If you want to run multiple *Portal Server*\ s or *UMC Server*\ s behind a load balancer,
   you need to run these commands on all Nubus for UCS nodes.

   Since all the nodes use the same OIDC client in this setup,
   make sure that the file :file:`/etc/umc-oidc.secret` has the same contents
   on each node and matches the client secret in :program:`Keycloak` for that client.

.. _ucs-operation-auth-sso-oidc-back-channel-sign-out:

Back-channel sign-out
~~~~~~~~~~~~~~~~~~~~~

If you use OIDC back-channel sign-out together with multiprocessing of the *Management UI*,
the *Management UI* needs a database for session storage to handle the session logout correctly.
You have enabled multiprocessing in the *Management UI*
if the UCR variable :envvar:`umc/http/processes` has a value greater than one (``> 1``).

If you have only one *UMC Server* without UMC multiprocessing,
you don't need to change the configuration.

To keep track of the sessions in the database for the *Management UI*,
you need to configure the database connection string
with the :program:`univention-management-console-settings` script,
as shown in :numref:`ucs-operation-auth-sso-oidc-back-channel-sign-out-sql-connection-optional-listing`.

However, if the *Portal* or the *Management UI*
use multiple Nubus for UCS nodes for load balancing,
or if the *Management UI* has a configuration for multiprocessing,
it's necessary to use a :program:`PostgreSQL` database
that all Nubus for UCS nodes can access.
In these cases, you must consider the following aspects:

#. PostgreSQL database server:

   You either need to provide a :program:`PostgreSQL` database yourself
   that all the *UMC Server*\ s have access to.

   Alternatively,
   you can install and configure :program:`PostgreSQL` on one of the Nubus for UCS nodes.
   As shown in the example in
   :numref:`ucs-operation-auth-sso-oidc-back-channel-sign-out-postgres-install-listing`,
   you can freely choose the values for
   ``db_user``, ``db_name``, and ``db_password``.
   ``db_host`` is a Nubus for UCS node with :program:`PostgreSQL` running.

   .. code-block:: console
      :caption: Example for installation of :program:`PostgreSQL`
      :name: ucs-operation-auth-sso-oidc-back-channel-sign-out-postgres-install-listing

      $ univention-install univention-postgresql
      $ su postgres -c "createdb db_name"
      $ su postgres -c "/usr/bin/createuser db_user"
      $ su postgres -c "psql db_name -c \"ALTER ROLE db_user WITH ENCRYPTED PASSWORD 'db_password'\""
      $ su postgres -c "psql umc -c \"GRANT ALL ON SCHEMA public TO umc;\""
      $ ucr set postgres15/pg_hba/config/host="umc umc 1x.2xx.0.0/16 md5"
      $ systemctl restart postgresql

#. Set the SQL connection URI on the :term:`UCS Primary Directory Node`,
   as shown in
   :numref:`ucs-operation-auth-sso-oidc-back-channel-sign-out-sql-connection-listing`.

   .. code-block:: console
      :caption: Set SQL connection URI
      :name: ucs-operation-auth-sso-oidc-back-channel-sign-out-sql-connection-listing

      $ univention-management-console-settings set \
         -u 'postgresql+psycopg2://db_user:db_password@db_host:5432/db_name'

#. Optional parameters for the database connection pool:

   :``Pool Size``: The number of connections to the database.
     Default value: ``5``.

   :``Max Overflow``: The maximum number of temporary connections.
     Default value: ``10``.

   :``Pool Timeout``: The number of seconds to wait for a connection to be available.
     Default value: ``30``.

   :``Pool Recycle``: The number of seconds after which a connection is recycled.
     Default value: ``-1``.

   With these default values, each UMC process can have up to 15 connections to the database.
   The total number of connections is: :math:`NumberOfServers \cdot NumberOfProcesses \cdot (PoolSize + MaxOverflow)`.

   Make sure that the database can handle the number of connections.
   You can adjust these parameters as shown in
   :numref:`ucs-operation-auth-sso-oidc-back-channel-sign-out-sql-connection-optional-listing`.

   .. code-block:: console
      :caption: Set optional parameters for the database connection pool
      :name: ucs-operation-auth-sso-oidc-back-channel-sign-out-sql-connection-optional-listing

      $ univention-management-console-settings set \
           -s 5 \
           -o 10 \
           -t 30 \
           -r 3600

#. Restart the *UMC Server* on all Nubus for UCS nodes with the command in
   :numref:`ucs-operation-auth-sso-oidc-back-channel-sign-out-restart-umc-listing`.

   .. code-block:: console
      :caption: Restart UMC server
      :name: ucs-operation-auth-sso-oidc-back-channel-sign-out-restart-umc-listing

      $ systemctl restart univention-management-console-server

.. important::

   If UCS involves more than one *UMC Server* instance,
   the feature for the refresh of the portal tabs on sign-out or session timeout
   requires :program:`PostgreSQL`.
   You can also use a local :program:`SQLite` database for one *UMC Server* with multiprocessing.
