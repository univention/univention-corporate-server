.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _domain-infrastructure-provisioning-service:

Provisioning Service
====================

The *Provisioning Service* is an event and messaging service
that can notify interested services about events in the LDAP directory service.
When data changes in the LDAP directory on the :term:`Primary Directory Node`,
the *Provisioning Service* receives a notification about the change
and notifies any subscribed services about the change.
In contrast to the Univention Directory Listener,
it provides the UDM representation of the change objects
instead of the LDAP representation.

This page describes the installation and configuration of the *Provisioning Service* in Nubus for UCS.
For more information on the inner workings of the *Provisioning Service*,
see :external+uv-nubus-kubernetes-architecture:ref:`component-provisioning-service`
in :cite:t:`uv-nubus-kubernetes-architecture`.

.. note::

   There are no services integrated into Nubus for UCS that use the *Provisioning Service*.
   You can create services that use the *Provisioning Service*
   according to
   :external+uv-nubus-customization:ref:`customization-api-provisioning`
   in :cite:t:`uv-nubus-kubernetes-customization`.

   .. FIXME: Clarify. Is the statement still true?

.. _domain-infrastructure-provisioning-service-installation:

Installation
------------

Univention App Center provides the *Provisioning Service* as an application.
Nubus for UCS doesn't install it by default.
You can install it on the :term:`Primary Directory Node` and on every :term:`Backup Directory Node`.
It isn't possible to install the *Provisioning Service* on other server system roles.
The *Provisioning Service* consists of the following apps:

:program:`provisioning-service`
   The :program:`provisioning-service` app is a container app
   that provides the main features of the *Provisioning Service*.

:program:`provisioning-service-backend`
   The :program:`provisioning-service-backend` app is a package based app
   that installs integration packages in Nubus for UCS.
   The App Center automatically installs it as a dependency of :program:`provisioning-service`.
   The packages include a listener module and host configuration for TLS encryption between multiple installations.

To install *Provisioning Service*, choose one of the following installation methods.
The App Center applies multiple settings to the *Provisioning Service*.
For a reference, see :ref:`domain-infrastructure-provisioning-service-app-settings`.

.. tab-set::

   .. tab-item:: App Center
      :sync: appcenter

      You can install the :program:`provisioning-service` app like any other app through Univention App Center.
      For general information about Univention App Center and how to use it for software installation,
      see :ref:`lifecycle-app-center`.

   .. tab-item:: Command line

      To install the app through the command line,
      use the command in
      :numref:`nubus-provisioning-service-install-listing`.

      .. code-block:: console
         :caption: Install *Provisioning Service* through command line
         :name: nubus-provisioning-service-install-listing

         $ univention-app install provisioning-service

.. _domain-infrastructure-provisioning-service-workflow:

Provisioning workflow
---------------------

The *Provisioning Service* delivers a stream of events about data changes in the LDAP directory service.
It uses the following components:

.. _domain-infrastructure-provisioning-service-workflow-listener:

Provisioning Listener
   A Univention Directory Listener module, which reacts to all LDAP operations and pushes
   these changes to the *Provisioning Service*.
   The Univention Directory Listener module :file:`nubus-provisioning.py` notifies the *Provisioning Service*.
   It runs on :term:`Primary Directory Node` only.

.. _domain-infrastructure-provisioning-service-workflow-transformer:

Provisioning UDM Transformer
   The *Provisioning UDM Transformer* transforms incoming LDAP level change events
   to UDM level provisioning events by calling the *UDM HTTP REST API*.
   It runs on :term:`Primary Directory Node` only.

.. _domain-infrastructure-provisioning-service-workflow-prefill:

Provisioning Prefill Service
   The *Provisioning Prefill Service* streams all UDM objects of the subscribed type
   to the subscribed consumer app.
   It runs on the :term:`Primary Directory Node` only.

.. _domain-infrastructure-provisioning-service-workflow-dispatcher:

Provisioning Dispatcher
   The *Provisioning Dispatcher* routes events about all UDM objects
   to the provisioning queues of subscribed apps.
   It runs on :term:`Primary Directory Node` and :term:`Backup Directory Node`.

.. _domain-infrastructure-provisioning-service-workflow-api:

Provisioning APIs
   The *Provisioning APIs* runs on the :term:`Primary Directory Node` and the :term:`Backup Directory Node`.
   It's a collection of various APIs for service registration to subscribe to events
   and messaging.

.. _domain-infrastructure-provisioning-service-workflow-nats:

Event streaming service
   :program:`NATS` handles the actual event streaming service.

On the :term:`Backup Directory Node` the *Provisioning Dispatcher* connects
to the event streaming service running on the :term:`Primary Directory Node`.
It streams data through a TLS encrypted connection.

.. seealso::

   :external+uv-nubus-kubernetes-architecture:ref:`component-provisioning-service`
      in :cite:t:`uv-nubus-kubernetes-architecture`
      for information about the architecture of the *Provisioning Service*

   :external+uv-nubus-customization:ref:`customization-api-provisioning`
      in :cite:t:`uv-nubus-kubernetes-customization`
      for information about how to use the *Provisioning Service*
      and create a subscription for a *Provisioning Consumer*.

.. _domain-infrastructure-provisioning-service-endpoints-and-ports:

Endpoints and ports
-------------------

The *Provisioning Service* provides endpoints and ports as outlined in
:numref:`domain-infrastructure-provisioning-service-endpoints-and-ports-table`.

You can access the *Provisioning API* locally through ``http://localhost:7777``,
or remotely through :samp:`https://{<Primary FQDN>}/univention/provisioning/`.

.. _domain-infrastructure-provisioning-service-endpoints-and-ports-table:

.. list-table:: Endpoints and ports
   :header-rows: 1
   :widths: 2 10

   * - Port
     - Purpose

   * - 4230
     - The :program:`stunnel` port.
       You can adjust it through the :envvar:`nats/stunnel/accept/port` UCR variable.

   * - 4222
     - NATS client connections.

   * - 7777
     - Provisioning APIs.

   * - 8222
     - NATS Monitoring endpoint.

.. important::

   The *Provisioning Dispatcher* needs access to the *UDM HTTP REST API* on port ``443``
   on :term:`Primary Directory Node` and :term:`Backup Directory Node`.

.. _domain-infrastructure-provisioning-service-app-log-files:

Provisioning Service log files
------------------------------

If you encounter problems with the *Provisioning Service*,
you can consult the following log files:

* The *Provisioning Service* containers write their logs to :file:`/var/log/syslog`.

* The :file:`nubus-provisioning.py` listener module
  that provides the *Provisioning Service* with information,
  writes logs to :file:`/var/log/univention/listener_modules/nubus-provisioning.log`.

* The :program:`stunnel` service
  that ensures TLS encryption between :term:`Primary Directory Node` and :term:`Backup Directory
  Node`,
  writes logs to :file:`/var/log/stunnel4/stunnel.log`.

.. _domain-infrastructure-provisioning-service-app-settings:

Provisioning Service settings
-----------------------------

The following references show the available settings within the
*Provisioning Service* app.
Univention recommends keeping the default values.

To change settings after the app installation,
use these steps:

#. Sign in to the *Management UI* with a user account in the ``Domain Admins`` group
   and go to :menuselection:`App Center --> Provisioning Service --> Manage Installations --> Select instance via checkbox --> ⋯ More --> App Settings`.

#. On the *Configure Provisioning Service* page,
   change the settings.

#. To apply the settings, click :guilabel:`Apply Changes`.

The App Center then *reinitializes* the containers for the *Provisioning Service* app.
*Reinitialize* means that the App Center throws away the running containers comprising the app
and creates a fresh set of containers with the just changed settings.

For some setting changes you need to restart the :program:`univention-directory-listener`.
Run the command in
:numref:`domain-infrastructure-provisioning-service-app-settings-reference-restart-listener-listing`.

.. code-block:: console
   :caption: Restart the *Directory Listener*
   :name: domain-infrastructure-provisioning-service-app-settings-reference-restart-listener-listing

   $ systemctl restart univention-directory-listener

.. _domain-infrastructure-provisioning-service-app-settings-reference:

App settings
~~~~~~~~~~~~

The *Provisioning Service* app has the following app settings.

.. envvar:: provisioning-service/udm-rest-api-host

   Fully qualified domain name (FQDN) of the UDM REST API host.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - Value from :envvar:`ldap/master`
        - Installation and app configuration

.. envvar:: provisioning-service/primary

   Fully qualified domain name (FQDN) of the :term:`Primary Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - Value from :envvar:`ldap/master`
        - Installation and app configuration

.. envvar:: nats/max_retry_count

   Number of times the
   :ref:`domain-infrastructure-provisioning-service-workflow-listener`
   re-tries to synchronize each transaction to the :ref:`domain-infrastructure-provisioning-service-workflow-nats`.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`domain-infrastructure-provisioning-service-app-settings-reference-restart-listener-listing`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - ``3``
        - Installation and app configuration

.. envvar:: nats/retry_delay

   The number of seconds to wait between each attempt to synchronize a transaction to the
   :ref:`domain-infrastructure-provisioning-service-workflow-nats`.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`domain-infrastructure-provisioning-service-app-settings-reference-restart-listener-listing`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - ``1``
        - Installation and app configuration

.. envvar:: nats/max_reconnect_attempts

   The maximum number of times to attempt to reconnect to the :ref:`domain-infrastructure-provisioning-service-workflow-nats`.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`domain-infrastructure-provisioning-service-app-settings-reference-restart-listener-listing`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - 3
        - Installation and app configuration

.. _domain-infrastructure-provisioning-service-ucr-variables:

UCR Variables
~~~~~~~~~~~~~

Additionally, the *Provisioning Service* considers the following :term:`UCR variables <UCR variable>`
that don't appear in the app settings.
Univention recommends keeping the default values.

.. envvar:: nats/stunnel/accept/port

   Listening port number of the :program:`stunnel`
   securing the :program:`NATS` connection
   between :term:`Primary Directory Node` and :term:`Backup Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - ``4230``
        - Installation and app configuration.

.. envvar:: nats/stunnel/connect/port

   Connection port of the :program:`stunnel`
   securing the connection
   between :ref:`domain-infrastructure-provisioning-service-workflow-dispatcher` on :term:`Backup Directory Node`
   and :program:`NATS` on :term:`Primary Directory Node`. Must match
   the :envvar:`nats/stunnel/accept/port` of the :term:`Primary Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - ``4230``
        - Installation and app configuration.

.. envvar:: nats/stunnel/cert

   Certificate for the :program:`stunnel` :program:`NATS` connection
   between :ref:`domain-infrastructure-provisioning-service-workflow-dispatcher` on a :term:`Backup Directory Node`
   and :program:`NATS` on :term:`Primary Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - :file:`/etc/univention/ssl/@%@ldap/master@%@/cert.pem`
        - Installation and app configuration.

.. envvar:: nats/stunnel/key

   Certificate key used for the :program:`stunnel` :program:`NATS` connection
   between :ref:`domain-infrastructure-provisioning-service-workflow-dispatcher` on a :term:`Backup Directory Node`
   and :program:`NATS` on :term:`Primary Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - :file:`/etc/univention/ssl/@%@ldap/master@%@/private.key`
        - Installation and app configuration.

.. envvar:: nats/stunnel/cacert

   The CA certificate used for the :program:`stunnel` :program:`NATS` connection
   between :ref:`domain-infrastructure-provisioning-service-workflow-dispatcher` on a :term:`Backup Directory Node`
   and :program:`NATS` on :term:`Primary Directory Node`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - :file:`/etc/univention/ssl/ucsCA/CAcert.pem`
        - Installation and app configuration.
