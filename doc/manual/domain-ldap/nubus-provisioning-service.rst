.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _nubus-provisioning-service:

Provisioning Service
====================

The *Provisioning Service* is an event and messaging service
that can notify interested services about events in the LDAP directory service.
When data changes in the LDAP directory on the |UCSPRIMARYDN|,
the *Provisioning Service* receives a notification about the change
and notifies any subscribed services about the change.
In contrast to the |UCSUDL|,
it provides the UDM representation of the change objects
instead of the LDAP representation.

This page describes the installation and configuration of the *Provisioning Service* in UCS.
For more information on the inner workings of the *Provisioning Service*,
see :external+uv-nubus-kubernetes-architecture:ref:`component-provisioning-service`
in :cite:t:`uv-nubus-kubernetes-architecture`.

.. note::

   There are no services integrated into UCS that make use of the *Provisioning Service*.
   You can create services that use the *Provisioning Service*
   according to
   :external+uv-nubus-kubernetes-customization:ref:`customization-api-provisioning`
   in :cite:t:`uv-nubus-kubernetes-customization`.

.. note::

   The *Provisioning Service* is part of Univention Nubus in the *Identity Store and Directory Service* component.
   For more information about Nubus, refer to :ref:`introduction-nubus`

.. _nubus-provisioning-service-install:

Installation
------------

Univention App Center provides the *Provisioning Service* as an application.
UCS doesn't install it by default.
You can install it on the |UCSPRIMARYDN| and on every |UCSBACKUPDN|.
It isn't possible to install the *Provisioning Service* on other server system roles.
The *Provisioning Service* consists of the following apps:

:program:`provisioning-service`
   The :program:`provisioning-service` app is a container app
   that provides the main features of the *Provisioning Service*.

:program:`provisioning-service-backend`
   The :program:`provisioning-service-backend` app is a package based app
   that installs integration packages in UCS.
   The App Center automatically installs it as a dependency of :program:`provisioning-service`.
   The packages include a listener module and host configuration for TLS encryption between multiple installations.

To install *Provisioning Service*, choose one of the following installation methods.
The App Center applies multiple settings to the *Provisioning Service*.
For a reference, see :ref:`nubus-provisioning-service-app-settings`.

.. tab-set::

   .. tab-item:: App Center
      :sync: appcenter

      You can install the :program:`provisioning-service` app like any other app through Univention App Center.
      For general information about Univention App Center and how to use it for software installation,
      see :ref:`software-appcenter`.

   .. tab-item:: Command line

      To install the app through the command line,
      use the command in
      :numref:`nubus-provisioning-service-install-listing`.

      .. code-block:: console
         :caption: Install *Provisioning Service* through command line
         :name: nubus-provisioning-service-install-listing

         $ univention-app install provisioning-service

.. _nubus-provisioning-service-workflow:

Provisioning workflow
---------------------

The *Provisioning Service* delivers a stream of events about data changes in the LDAP directory service.
It uses the following components:

.. _nubus-provisioning-service-workflow-listener:

Provisioning Listener
   A |UCSUDL| listener module, which reacts to all LDAP operations and pushes
   these changes to the *Provisioning Service*.
   The |UCSUDL| module :file:`nubus-provisioning.py` notifies the *Provisioning Service*.
   It runs on |UCSPRIMARYDN| only.

.. _nubus-provisioning-service-workflow-transformer:

Provisioning UDM Transformer
   The *Provisioning UDM Transformer* transforms incoming LDAP level change events
   to UDM level provisioning events by calling the *UDM HTTP REST API*.
   It runs on |UCSPRIMARYDN| only.

.. _nubus-provisioning-service-workflow-prefill:

Provisioning Prefill Service
   The *Provisioning Prefill Service* streams all UDM objects of the subscribed type
   to the subscribed consumer app.
   It runs on the |UCSPRIMARYDN| only.

.. _nubus-provisioning-service-workflow-dispatcher:

Provisioning Dispatcher
   The *Provisioning Dispatcher* routes events about all UDM objects
   to the provisioning queues of subscribed apps.
   It runs on |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _nubus-provisioning-service-workflow-api:

Provisioning API
   The *Provisioning API* runs on the |UCSPRIMARYDN| and the |UCSBACKUPDN|
   and is the API that applications use to subscribe to events.

.. _nubus-provisioning-service-workflow-nats:

NATS
   :program:`NATS` handles the actual event streaming service.

On the |UCSBACKUPDN| the *Provisioning Dispatcher* connects
to the :program:`NATS` Service running on the |UCSPRIMARYDN|.
It streams data through a TLS encrypted connection.

.. seealso::

   :external+uv-nubus-kubernetes-architecture:ref:`component-provisioning-service`
      in :cite:t:`uv-nubus-kubernetes-architecture`
      for information about the architecture of the *Provisioning Service*

   :external+uv-nubus-kubernetes-customization:ref:`customization-api-provisioning`
      in :cite:t:`uv-nubus-kubernetes-customization`
      for information about how to use the *Provisioning Service*
      and create a subscription for a *Provisioning Consumer*.

.. _nubus-provisioning-service-endpoints-and-ports:

Endpoints and ports
-------------------

The *Provisioning Service* provides endpoints and ports as outlined in
:numref:`nubus-provisioning-service-endpoints-and-ports-table`.

You can access the *Provisioning API* locally through ``http://localhost:7777``,
or remotely through :samp:`https://{<Primary FQDN>}/univention/provisioning/`.


.. _nubus-provisioning-service-endpoints-and-ports-table:

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
     - Provisioning API.

   * - 8222
     - NATS Monitoring endpoint.

.. important::

   The *Provisioning Dispatcher* needs access to the *UDM HTTP REST API* on port ``443``
   on |UCSPRIMARYDN| and |UCSBACKUPDN|.

.. _nubus-provisioning-service-app-log-files:

Provisioning Service log files
------------------------------

If you encounter problems with the *Provisioning Service*,
you can consult the following log files:

* The *Provisioning Service* containers write their logs to :file:`/var/log/syslog`.

* The :file:`nubus-provisioning.py` listener module
  that provides the *Provisioning Service* with information,
  writes logs to :file:`/var/log/univention/listener_modules/nubus-provisioning.log`.

* The :program:`stunnel` service
  that ensures TLS encryption between |UCSPRIMARYDN| and |UCSBACKUPDN|,
  writes logs to :file:`/var/log/stunnel4/stunnel.log`.

.. _nubus-provisioning-service-app-settings:

Provisioning Service settings
-----------------------------

The following references show the available settings within the
*Provisioning Service* app.
Univention recommends keeping the default values.

To change settings after the app installation,
sign in to the UCS management system with a user account in the ``Domain Admins`` group
and go to :menuselection:`App Center --> Provisioning Service --> Manage Installations --> Select instance via checkbox --> ⋯ More --> App Settings`.
On the *Configure Provisioning Service* page,
you can change the settings
and apply them to the app by clicking :guilabel:`Apply Changes`.

The App Center then *reinitializes* the Docker containers for the *Provisioning Service* app.
*Reinitialize* means that the App Center throws away the running containers comprising the app
and creates a fresh set of containers with the just changed settings.

For some setting changes you need to restart the :program:`univention-directory-listener`.
Run the command in :numref:`nubus-provisioning-service-app-settings-reference-restart-listener-listing`.

.. code-block:: console
   :caption: Restart the *Directory Listener*
   :name: nubus-provisioning-service-app-settings-reference-restart-listener-listing

   $ systemctl restart univention-directory-listener

.. _nubus-provisioning-service-app-settings-reference:

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

   Fully qualified domain name (FQDN) of the |UCSPRIMARYDN|.

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
   :ref:`nubus-provisioning-service-workflow-listener`
   re-tries to synchronize each transaction to the provisioning NATS service.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`nubus-provisioning-service-app-settings-reference-restart-listener-listing`.

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

   The number of seconds to wait between each attempt to synchronize a transaction to the provisioning NATS service.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`nubus-provisioning-service-app-settings-reference-restart-listener-listing`.

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

   The maximum number of times to attempt to reconnect to the NATS service.
   After you change this setting
   you need to restart the :program:`univention-directory-listener`,
   see :numref:`nubus-provisioning-service-app-settings-reference-restart-listener-listing`.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - 3
        - Installation and app configuration

.. envvar:: provisioning-service/log/level

   The log level for the Provisioning Service.
   This affects the container based service components.
   Possible values: ``CRITICAL``, ``ERROR``, ``WARNING``, ``INFO``, ``DEBUG``.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - No
        - ``WARNING``
        - Installation and app configuration

.. _nubus-provisioning-service-ucr-variables:

UCR Variables
~~~~~~~~~~~~~

Additionally, the *Provisioning Service* considers the following UCR variables
that don't appear in the app settings.
Univention recommends keeping the default values.

.. envvar:: nats/stunnel/accept/port

   Listening port number of the :program:`stunnel`
   securing the :program:`NATS` connection
   between |UCSPRIMARYDN| and |UCSBACKUPDN|.

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
   between *Provisioning Dispatcher* on |UCSBACKUPDN|
   and :program:`NATS` on |UCSPRIMARYDN|. Must match
   the :envvar:`nats/stunnel/accept/port` of the |UCSPRIMARYDN|.

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
   between *Provisioning Dispatcher* on a |UCSBACKUPDN|
   and :program:`NATS` on |UCSPRIMARYDN|.

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
   between *Provisioning Dispatcher* on a |UCSBACKUPDN|
   and :program:`NATS` on |UCSPRIMARYDN|.

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
   between *Provisioning Dispatcher* on a |UCSBACKUPDN|
   and :program:`NATS` on |UCSPRIMARYDN|.

   .. list-table::
      :header-rows: 1
      :widths: 2 5 5

      * - Required
        - Default value
        - Set

      * - Yes
        - :file:`/etc/univention/ssl/ucsCA/CAcert.pem`
        - Installation and app configuration.
