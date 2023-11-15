.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-udm:

Univention Directory Manager (UDM)
==================================

This section describes the technical details for |UDM|. For a general overview
about the UCS management system and the role of |UDM|, see
:ref:`component-management-system`.

You find the source code for |UDM| at
:uv:src:`management/univention-directory-manager-modules/`.

Other packages in |UCS| can also define UDM modules. The respective packages
include the sources for their UDM modules. For example, the following packages
also provide UDM modules:

* :ref:`component-app-center` at :uv:src:`management/univention-appcenter/`

* :ref:`services-ucs-portal` at :uv:src:`management/univention-portal/`

* S4 Connector at :uv:src:`services/univention-s4-connector/`

.. TODO : Add reference to S4 connector
   * :ref:`services-samba-s4-connector` at :uv:src:`services/univention-s4-connector/`

.. _services-udm-architecture:

UDM architecture
----------------

.. index::
   pair: udm; umc
   single: udm; architecture

:numref:`architecture-model-udm` shows the architecture for |UDM|. A description
of the elements follows.

.. _architecture-model-udm:

.. figure:: /images/UDM-architecture.*

   Architecture of |UDM|

.. index::
   pair: ldap directory; udm
   single: model; ldap directory

LDAP directory
   The data persistence layer consists of the LDAP directory, that provides the
   domain database, the persistence layer and data source for |UDM|. For
   communication with the LDAP directory, |UDM| uses the *Lightweight Directory
   Access Protocol (LDAP)*.

|UDM| uses a two layer architecture for abstraction as shown in
:numref:`architecture-model-udm`. Except for the *LDAP directory*, all shown
elements belong to |UDM|. The first abstraction layer at the bottom is the *UDM
Python library* with the following elements:

.. index::
   single: model; udm python library
   single: python library; udm
   single: python; udm
   single: udm; udm python library

UDM Python library
   Provides the library for abstraction and the environment for *UDM syntax*,
   *UDM modules*, and *UDM hooks*. *UDM Python library* uses the *LDAP
   directory*. You can imagine something similar to an object relational mapper
   for SQL. *UDM Python library* provides Python modules and classes below
   :py:mod:`univention.admin.* <univention.admin>`:

.. index::
   single: udm; syntax
   single: model; udm syntax

UDM Syntax
   UDM syntax provides the following capability:

   * Perform syntax validation on user input data.

   * Present static values from a predefined list of possible values.

   * Calculate possible values dynamically upon use.

   * Specify the layout and widget type for presentation in |UMC|.

.. index::
   pair: udm; hooks
   single: model; udm modules
   single: udm modules

UDM modules
   |UDM| modules translate LDAP objects to UDM objects and back. They ensure
   data consistency, validate user input, implement process logic and improve
   the usability of |UCS|.

   * For more information about UDM modules, refer to
     :ref:`services-udm-modules`.

   * For more information about UDM data, refer to :ref:`services-udm-data`.

.. index::
   single: model; udm hooks

UDM hooks
   UDM hooks are Python classes with methods that can integrate into existing
   UDM modules together with *extended attributes*. They offer an alternative to
   customize |UDM|.

   .. TODO Add when hooks are ready: For more information, refer to :ref:`services-hooks`.

The second abstraction layer in :numref:`architecture-model-udm` uses the *UDM
Python library* and offers *UDM in UMC*, *UDM HTTP REST API*, the *UDM CLI daemon*, the
*UCS\@school library*, and the *UDM Simple API*.

.. index::
   single: udm; udm in umc
   single: model; udm in umc

UDM in UMC
   Runs the UDM modules inside |UMC| and presents them to the user over HTTP
   through the web browser. It creates one process per user session for all UDM
   modules. *UDM in UMC* uses the *UDM Python library*.

.. index::
   pair: udm http rest api; udm
   single: model; udm http rest api

UDM HTTP REST API
   Provides the HTTP REST API interface to |UDM| as a separate service. |UDM|
   offers HTTP access through the UDM HTTP REST API to use |UDM| through a
   remote interface.

   .. TODO Add when rest api is ready: For more information about the architecture, refer to :ref:`services-rest-api`.

.. index::
   single: udm; CLI
   single: model; udm cli daemon

UDM CLI Daemon
   Provides the command-line interface to |UDM| through one system wide process
   for each user. The process terminates itself after a default idle time of 10
   minutes. The command-line interface uses the *UDM Python library*.

   .. TODO : Corresponding UCR variable is directory/manager/cmd/timeout. But
      not mentioned in other documents.

.. index::
   single: udm; ucs@school library
   single: model; ucs@school library

UCS\@school library
   Provides an abstraction in Python for UCS\@school. The UCS\@school library
   uses the *UDM Python library*.

.. index::
   single: udm; UDM simple API
   single: model; udm simple api

UDM Simple API
   Allows to use |UDM| capability and objects directly in Python programs. For
   example, :ref:`services-ucs-portal` uses the API. *UDM Simple API* provides
   Python modules and classes below :py:mod:`univention.udm.* <univention.udm>`.

As mentioned before, |UDM| is highly customizable to the needs of environments,
custom services and apps. Custom UDM modules, extended attributes and UDM hooks
offer different possibilities for the customization of UDM.

.. seealso::

   Administrators, refer to :cite:t:`ucs-manual`:

   * :ref:`central-extended-attrs`

   * :ref:`central-udm`

.. seealso::

   Software developers and system engineers, refer to
   :cite:t:`developer-reference`:

   * :ref:`uv-dev-ref:udm-syntax`

   From :cite:t:`ucs-python-api`:

   * :py:mod:`univention.admin`

   * :py:mod:`univention.udm`

.. _services-udm-dependencies:

Dependencies for UDM
--------------------

.. index::
   pair: dependency; udm
   single: udm dependency; udm python library
   single: udm dependency; udm syntax
   single: udm dependency; udm modules
   single: udm dependency; udm hooks

|UDM| depends on LDAP. You can resolve the other detailed dependencies with the
package manager.

.. TODO : Add reference when LDAP is ready:
   |UDM| depends on :ref:`services-ldap`. You can resolve the other detailed
   dependencies with the package manager.

The following services in UCS need UDM:

* UCS\@school library

* Active Directory Connector

* S4 Connector

  .. TODO : Readd the cross references:
     * :ref:`services-samba-ad-connector`

     * :ref:`services-samba-s4-connector`

* :ref:`services-ucs-portal`

Following the chain, *UDM in UMC* and *UDM HTTP REST API* wouldn't work without
|UDM| either. From the items mentioned in :ref:`services-udm-architecture` and
:numref:`architecture-model-udm`, |UDM| needs the following to work properly:

* *UDM Python library*
* *UDM syntax*
* *UDM modules*
* *UDM hooks*

And |UDM| offers its capability to the following items:

* *Python UDM API*
* *UDM CLI daemon*
* *UCS\@school library*

.. _services-udm-modules:

UDM modules
-----------

.. index:: ! udm modules, udm; ldap objects
   pair: udm modules; python

|UDM| modules represent a set of LDAP object classes and their corresponding
attributes in UDM objects. They ensure data consistency, validate user input,
implement process logic and improve the usability of |UCS|.

UDM modules exist for almost every LDAP object class. For example, UDM objects
``users/user`` represent different LDAP object classes like ``person``,
``organizationalPerson``, ``inetOrgPerson``, ``posixAccount``, or
``shadowAccount``. Another example is the password field at a UDM object
``users/user``, that creates several password hash types in the different LDAP
object classes for users. UDM presents one password to the user. In the
background it ensures password consistency for different services, that need
different password hash types.

.. index::
   pair: directory listener; udm modules

.. TODO : Add cross reference to listener in the section below, once ready.

Python is the programming language for UDM modules. During installation UDM
modules register themselves in the LDAP directory. The UCS domain replicates the
UDM modules to UCS systems across the domain. On the UCS systems, the Univention
Directory Listener writes the UDM modules to the systems' file system. The
replication ensures the availability of all UDM modules in the UCS domain alike.


Domain administrators can grant permission to use particular UDM modules in UMC
to other users. UDM modules access the LDAP directory with the permissions of
the user so that LDAP *access control lists* for read and write actions apply to
the user.

.. seealso::

   :ref:`uv-dev-ref:udm-modules`
      For information about UDM modules for software developers in
      :cite:t:`developer-reference`.

.. _services-udm-data:

UDM data
--------

.. index:: ! udm; ldap objects
   single: udm; properties
   single: udm; attributes
   single: udm; objects
   single: ldap; objects
   single: udm; mapping
   single: model; ldap object
   single: model; udm modules
   single: model; udm objects

Talking about UDM modules requires a distinction between data describing a UDM
object and an LDAP object:

* The term *properties* refers to data fields in UDM objects.

* The term *attributes* refers to data fields in LDAP objects.

UDM modules map between LDAP objects and UDM objects. They format data upon read
and write operations to and from the LDAP directory for representation to the
user as shown in :numref:`services-udm-data-model`. UDM modules are in the
center of the data mapping and emphasize their translation role. For example,
widgets in |UMC| show a human readable representation of the data. Fields that
represent a date value offer a calendar widget to the user.

.. _services-udm-data-model:

.. figure:: /images/UDM-modules-data.*

   UDM modules map data between LDAP objects and UDM objects

.. index:: ! extended attributes, ! udm; extended attributes

Extended attributes provide the capability to add and customize properties in
|UDM|. They define a mapping between UDM properties and LDAP attributes.

.. seealso::

   :ref:`central-extended-attrs`
      How to use extended attributes, :cite:t:`ucs-manual`
