.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-app-center:

App Center service
==================

.. index::
   single: app center; architecture overview
   single: app center; python app center library
   single: python library; app center

This section describes the architecture of the App Center service focused solely
on |UCS|.

For a general overview of the App Center, its ecosystem, the participating
actors, and the infrastructure, see :ref:`univention-app-ecosystem`. For the
overview of the App Center as product component, see
:ref:`component-app-center`.

You can find the source code at :uv:src:`management/univention-appcenter/`.

:numref:`services-app-center-architecture-overview` shows the architecture
overview of the App Center on a UCS system.

.. _services-app-center-architecture-overview:

.. figure:: /images/App-Center-architecture-overview.*
   :width: 600 px

   Architecture overview of the App Center on a UCS system

For the abstract context description about the first two rows in
:numref:`services-app-center-architecture-overview`, refer to
:ref:`component-app-center`.

In the notation in :numref:`services-app-center-architecture-overview` the
application service *App Center Service* summarizes all behavior that relates to
the App Center and apps on a |UCS| system. The center piece for all behavior in
the *App Center* are the *App Center actions* that use the *Python App Center
library* to do "stuff" with *App*\ s.

The App Center is a complex component in UCS. As you continue reading, the
concepts unfold and reveal their internal parts.

.. seealso::

   :py:mod:`Python App Center library <univention.appcenter>`
      for detailed information about the Python library for the App Center in
      :cite:t:`ucs-python-api`.

.. _services-app-center-interfaces:

App Center interfaces
---------------------

.. index::
   single: app center; interfaces
   single: app center; http/https
   single: app center; terminal / ssh
   single: interfaces; http/https
   single: interfaces; terminal / ssh
   single: UMC modules; app center in UMC
   single: UMC modules; Apps in UMC
   single: command; univention-app
   single: app center; command univention-app
   single: app; presentation

First, this section continues with the App Center connections to the external
world. :numref:`services-app-center-interfaces-model` shows the interfaces to
the user for the App Center and how the App Center relates to other parts of
UCS.

.. _services-app-center-interfaces-model:

.. figure:: /images/App-Center-interfaces-to-user.*

   App Center interfaces to the user

   The figure extends :numref:`component-app-center-architecture-component`.

The left side shows the path for the web interface of the App Center. Like many
other components, the App Center uses :ref:`services-umc` for the web interface.
The App Center provides the following :ref:`services-umc-modules`:

App Center in UMC
   The UMC module *App Center in UMC* provides the web interface to the user.
   Administrators can list, show, install, update, and remove apps. It presents
   all available apps to the administrator in a nice overview. It's also
   responsible for the app presentation with information like description,
   screenshots and videos, contact and app provider information.

Apps in UMC
   The UMC module *Apps in UMC* provides a proper view in the UCS management
   system for every installed app. It shows the app description, detailed
   information and offers actions like update or remove on the app to the
   administrator.

The right side shows the path to the command line interface of the App Center.

The items *App Center*, *Python App Center library*, and *App* in the middle are
the core of the App Center. The following sections describe them in more detail.

.. seealso::

   :ref:`app-presentation`
      for information about how app providers can define the data for app
      presentation in :cite:t:`ucs-app-center`.

   :uv:src:`management/univention-appcenter/umc/`
      for the source code of the UMC module *App Center in UMC*.

.. _services-app-center-actions:

App Center actions
------------------

.. index::
   single: app actions; install
   single: app actions; remove
   single: app actions; upgrade
   single: app actions; update
   single: app actions; start
   single: app actions; stop
   single: app actions; restart
   single: app actions; available actions
   single: directory listener; app center
   single: lifecycle management

*App Center actions* are the center piece for all behavior in the *App Center*.
Figure :numref:`services-app-center-actions-model` shows the most important
actions.

.. _services-app-center-actions-model:

.. figure:: /images/App-Center-architecture-actions.*

   App Center actions

To get a list of all actions, take a look into the checked out source code in
the directory :uv:src:`management/univention-appcenter/python/` of the UCS
repository and run the following command:

.. code-block:: console
   :caption: Get a list of available *App Center actions* from the sources

   $ find | grep actions

The core actions that administrators encounter when working with |UCS| are
actions to manage the app lifecycle and control their operational status. These
are actions such as:

* *App install*
* *App remove*
* *App upgrade*
* *App start*
* *App stop*
* *App restart*
* *App update*

And the App Center has other actions, for example, they run during installation
like the *App Center database integration* or handle a listener module dedicated
to the app. Furthermore, app developers use the *App Center Dev actions* during
app development.

The *App Center actions*\ ' purpose is manifold:

* They abstract lifecycle actions for apps for the various distribution flavors
  like *Package based app* and *Docker based app*.

* They hide the complexity of lifecycle management and standardize the needed
  procedures.

.. seealso::

   :ref:`app-center-ecosystem-apps`
      for information about the various distribution flavors *Package based app*
      and *Docker based app*.

.. _services-app-center-cache:

App Center apps cache
---------------------

.. index::
   single: app center; apps cache
   single: app; metadata
   single: app actions; update
   pair: cache; apps cache
   single: cache; command univention-app update
   single: univention-app; update
   single: JSON; app metadata
   see: file formats; JSON

This section covers the *Apps Cache*, a part of the *App Center* that exists on
every |UCS| system. :numref:`services-app-center-cache-model` shows the *Apps
Cache* relationship to the *App Center actions*.

.. _services-app-center-cache-model:

.. figure:: /images/App-Center-app-cache.*
   :width: 500 px

   App Center *Apps cache*

The App Center has the action *App update* that downloads information from the
*App repository* and writes the *Apps Cache* on a UCS system. It has the
following purposes:

* Download all the *App metadata* from the *App repository*. For information
  about the infrastructure, refer to :ref:`app-center-infrastructure`.

* Consolidate the app metadata in a JSON file.

.. index::
   single: directory; /var/cache/univention-appcenter
   single: cache; /var/cache/univention-appcenter

The app metadata locates in the directory
:file:`/var/cache/univention-appcenter/` on a UCS system. The data from the
*Apps Cache* is then available to all other *App Center actions* that need any
kind of information related to apps. For example, the UMC module *App Center in
UMC* reads the data from the *Apps Cache* to display it in the web interface.

.. _services-app-center-integration:

App integration
---------------

The App Center offers various integration points for apps to simplify the app
setup and the integration into the UCS environment.

.. _services-app-center-integration-web-serber:

Web server integration
~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: integration; web server
   see: integration; app center integration
   single: app center integration; web server
   single: app center integration; proxy server

For apps that offer their own web interface, the App Center provides a web
server integration as shown in
:numref:`services-app-center-integration-web-server-model`.

.. _services-app-center-integration-web-server-model:

.. figure:: /images/App-Center-integration-web-server.*
   :width: 600 px

   App Center web server integration

The *App Center web server integration* appends the *Web server configuration*
and adds the path to the app's web interface. The procedure uses
:ref:`services-ucr`. The *App Center web server integration* removes the
appended configuration upon app removal.

Apps can also provide a complex web server integration by adding their own
configuration to the *HTTP web server*. App developers handle the configuration
lifecycle on their own in the app.

.. seealso::

   :ref:`create-app-with-docker-web-interface`
      for more information about how to expose the app's web interface in
      :cite:t:`ucs-app-center`.

.. _services-app-center-integration-portal:

Portal integration
~~~~~~~~~~~~~~~~~~

Apps that offer a web interface and use the :ref:`web server integration
<services-app-center-integration-web-server-model>` automatically use the portal
integration to add a tile to the :ref:`UCS portal <services-ucs-portal>`, as
shown in :numref:`services-app-center-integration-portal-model`.

.. _services-app-center-integration-portal-model:

.. figure:: /images/App-Center-integration-portal.*
   :width: 600 px

   App Center portal integration

Upon installation, the App Center adds a portal tile with the icon, name, and
link to the app's web interface. Upon removal, the App Center removes the portal
tile.

.. _services-app-center-integration-database:

Database integration
~~~~~~~~~~~~~~~~~~~~

.. index::
   single: integration; database
   single: app center integration; database
   single: app center integration; MariaDB
   single: app center integration; PostgreSQL
   single: MariaDB; app center integration
   single: MariaDB; maintenance
   single: PostgreSQL; app center integration
   single: PostgreSQL; maintenance
   single: docker; custom database integration
   single: maintenance effort; database

For apps that need a |RDBMS| like *MariaDB* or *PostgreSQL* the App Center
installs the respective packages from the UCS package repository during app
installation, as shown in
:numref:`services-app-center-integration-database-model`.

.. _services-app-center-integration-database-model:

.. figure:: /images/App-Center-integration-database.*
   :width: 600 px

   App Center database integration

Apps using the databases provided with |UCS| benefit from the following
advantages:

* Univention maintains the packages for the databases and provides security
  updates.

* The databases integrate with the UCS system. For example, the App Center
  creates a database for the app together with a database user and password.

* The App Center provides the connection settings to the app. The app can start
  with creating the database schema.

Nevertheless, the *App Center database integration* has the following
limitations:

* UCS installs the |RDBMS| on the same host as the app and creates one database.

* The App Center doesn't use the |RDBMS| on a remote host or in a Docker
  environment.

* Apps have limited possibilities to configure the |RDBMS|.

* If the UCS system with the app has multiple apps installed that use a
  database, they share the |RDBMS| and its configuration.

Docker based apps, that need more flexibility, can provide their app as *Multi
container app* and add the |RDBMS| as Docker container with the required
configuration. The app provider is responsible for maintenance and security
updates for the |RDBMS| as Docker container.

:numref:`services-app-center-integration-database-maintenance-model` shows the
maintenance relations for the |RDBMS|. Although the model might imply that either
role maintains the database software, it's not the case. Instead, they cover the
distribution of the |RDBMS|.

.. _services-app-center-integration-database-maintenance-model:

.. figure:: /images/App-Center-database-maintenance.*
   :width: 600 px

   Maintenance of databases for Apps

   Consider the *OR* junction as *XOR* for the realization relation.

.. seealso::

   :ref:`create-app-with-docker-database`
      for more information about how to configure the app integration in an app
      in :cite:t:`ucs-app-center`.

.. _services-app-center-integration-identity-management:

Identity management integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: app center integration; identity management
   single: identity management; push method
   single: identity management; pull method
   pair: app center integration; user provisioning
   single: app center integration; user authentication
   pair: app center integration; directory listener

Many app providers integrate their app with the identity management in |UCS|.
The identity management integration consists of the following aspects:

User provisioning
   Provisioning means that the app gains knowledge about user account
   information and can, for example, create a user account in its own data
   structure and map it with the user account in the UCS identity management.
   Each app handles the mapping individually.

   The preferred provisioning method is *push*. Upon changes in the LDAP
   directory, the Univention Directory Listener creates information for the app
   to handle.

   .. TODO : Add link to directory listener, after the section is done.

   In contrast, the pull method through direct LDAP connection requires periodic
   pulls. The app must then identify and handle changes on its own.

User authentication
   Authentication means that the app uses one of the different authentication
   protocols in UCS like for example Kerberos, LDAP, SAML, or OpenID Connect.

   .. TODO : Once the chapters about the authentication protocols exist, convert
      them to cross-references.

To use the identity management integration in the app, the app developer can
activate it in the app metadata.

:numref:`services-app-center-integration-identity-management-push-model` shows
the App Center generating the listener module upon app installation for user
provisioning using the *push* method. The key items have a less strong filled
background color.

.. _services-app-center-integration-identity-management-push-model:

.. figure:: /images/App-Center-integration-identity-management.*

   *Register App directory listener* for user provisioning with *push* method

Register App directory listener
   Upon app installation, the App Center generates a listener module for the app
   and starts a service for the Univention Directory Listener.

   * *Register App directory listener* creates the artifact *Listener module for
     app*

   * *Listener modules for app* realizes the service *Listener Module for app*.

   * The service *Listener module service* runs the listener module for the app
     and belongs to the service *Univention Directory Listener*.

   For example, on a UCS system with five installed apps that use the identity
   management integration, the App Center generates five listener modules and
   services.

.. index:: JSON; app directory listener, listener; app directory listener

Listener module service
   The listener listens for changes in the LDAP directory service. The listener
   module consists of two parts:

   #. Part one creates change information relevant to the app based on changes
      in the LDAP directory. Such changes are, for example, *user account
      created*, *user account modified*, or *user account removed*.

   #. Part two takes the information about the changes and creates a JSON file,
      the artifact *Listener data JSON for app*, with information about the user
      account and about the kind of change. It periodically looks for the file
      from part one to generate the JSON file.

Listener data JSON for app
   Is the artifact created by the *Listener module service*. From an
   architecture perspective the artifact realizes the data object *IDM data for
   app*.

Provision users to app
   *Provision users to app* reads the *IDM data for app*, handles them
   accordingly, and writes the relevant information to the *App's user
   database*. For example, the app creates a user account in its database to
   internally refer to the user. The *Installed app*, that has *Provision users
   to app* assigned, is responsible to handle the JSON files written by the
   *Listener module service*.

.. seealso::

   For app software developers, refer to the following content in
   :cite:t:`ucs-app-center`:

   * :ref:`connection-idm` for information about how to connect an app with the
     identity management.

   * :ref:`provisioning`

     * :ref:`provisioning-pull`

     * :ref:`provisioning-push`

   * :ref:`authentication`

     * :ref:`authentication-ldap`

     * :ref:`authentication-kerberos`

.. _services-app-center-integration-extended-attributes:

Extended attributes
~~~~~~~~~~~~~~~~~~~

.. index::
   pair: extended attributes; app center integration

The App Center uses *extended attributes* for every app upon installation when
the app requires the administrator to enable user accounts for the app.

Extended attributes require an LDAP schema extension. The App Center creates that
schema extension automatically and registers it in the LDAP directory service.
And it also generates the extended attribute accordingly to use the extra fields
added with the schema extension and map them to respective fields in UDM.

For more information about extended attributes from the architecture
perspective, refer to :ref:`services-udm-data`.

Beyond the default schema extension, the App Center also registers schema
extensions provisioned with the app. Apps that use the LDAP directory as their
user database make use of schema extensions and extended attributes to enable a
respective user administration for the system administrator. An LDAP schema
extension ensures that the third party software can use the required LDAP
attributes.

.. seealso::

   Administrators refer to the following content in :cite:t:`ucs-manual`:

   :ref:`central-extended-attrs`
      How to use extended attributes

.. seealso::

   App software developers, refer to the following content in
   :cite:t:`ucs-app-center`:

   :ref:`user-rights-management`
      for more information about user rights management for apps.

.. _services-app-center-dependencies:

Dependencies for the App Center
-------------------------------

.. index::
   pair: dependency; app center

As complex component in UCS, the service *App Center* has the following dependencies:

* :ref:`services-ucr`
* :ref:`services-udm`
* :ref:`services-umc`
* Univention Directory Listener
* :ref:`services-ucs-portal`
* Univention updater
* *Docker.io* with the *Docker Engine* and *Docker compose*

.. TODO : Add references, once ready: Univention Directory Listener, Updater

:numref:`services-app-center-dependency-model` shows the direct dependencies in
the model.

.. _services-app-center-dependency-model:

.. figure:: /images/App-Center-dependencies.*
   :width: 650 px

   Dependencies of the App Center

The dependency to the *Univention updater* comes from the App Center's handling
of the *Package based Apps* and for example the *App Center database
integration*.
