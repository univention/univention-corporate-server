.. SPDX-FileCopyrightText: 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-migration-guardian:

******************************************************
Migrate from the local guardian to univention-guardian
******************************************************

So far, UDM has evaluated the permissions of delegative administration
with the *local guardian*, a component inside UDM.
With UCS 5.2-8, UDM can use *univention-guardian* instead,
which is a central policy decision point based on Cerbos.
Other services can use univention-guardian with the same roles
and get the same authorization decisions.

.. important::

   With UCS 5.2-8, univention-guardian is available as an experimental feature.
   Its behavior, the role definition format, and the configuration
   may still change.

.. warning::

   The local guardian is deprecated.
   UCS 5.3-0 no longer supports it.
   After the update to UCS 5.3-0,
   delegative administration with the local guardian stops working.

   Use UCS 5.2-8 to test univention-guardian and to migrate your environment.
   If you encounter problems during or after the migration,
   give feedback as described in :ref:`da-feedback`.
   Your feedback helps Univention to resolve the problems before UCS 5.3-0.

This section describes how to switch an existing environment
from the local guardian to univention-guardian:

#. :ref:`da-migration-guardian-before`
#. :ref:`da-migration-guardian-install`
#. :ref:`da-migration-guardian-custom-roles`
#. :ref:`da-migration-guardian-generate`
#. :ref:`da-migration-guardian-switch`
#. :ref:`da-migration-guardian-verify`

.. _da-migration-guardian-before:

Before you begin
================

Role assignments don't change.
The roles in the ``guardianRoles`` property of user objects
and in the ``guardianMemberRoles`` property of group objects
keep their names and contexts,
for example ``udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen,${ldap_base}``.
You don't need to modify user or group objects.

The role assignments only stay unchanged
for the migration to univention-guardian with UCS 5.2-8.
The way you assign roles to users and groups
will change with or after UCS 5.3-0.
The documentation of that release will describe the necessary changes.

.. TODO: describe the new role assignment (role mappings) once the design is final.

Make sure that your environment meets the following requirements:

* The |UCSPRIMARYDN| and every |UCSBACKUPDN|
  run UCS 5.2-8 or later with the latest errata updates.

* You have a backup of your role definition files,
  for example :file:`/etc/custom-udm-roles.policy`.

.. important::

   Test the migration in a test environment first.
   The evaluation of some rules differs
   between the local guardian and univention-guardian.
   For details, see :ref:`da-migration-guardian-differences`.

.. _da-migration-guardian-install:

Install univention-guardian
===========================

Install the package :program:`univention-guardian-server` on the |UCSPRIMARYDN|
and on every |UCSBACKUPDN|,
as shown in :numref:`da-migration-guardian-install-listing`.

.. code-block:: console
   :caption: Install univention-guardian
   :name: da-migration-guardian-install-listing

   $ univention-install univention-guardian-server

On each of these systems,
UDM sends its authorization requests to univention-guardian on the same system.
The UCR variable ``directory/manager/delegative-administration/cerbos/url``
already points to it with its default value ``http://localhost:3592``,
so you don't need to change the variable.

.. _da-migration-guardian-custom-roles:

Migrate custom roles
====================

The role definition format doesn't change.
For details about the format, see :ref:`da-concepts-role-definition`.
The update to UCS 5.2-8 installs the default roles
in :file:`udm-default-authorization-roles.policy`.
You only need to migrate your own role definition files.

To migrate your role definition files,
copy them to the directory :file:`/usr/share/univention-directory-manager-modules/policies/`
on the |UCSPRIMARYDN| and on every |UCSBACKUPDN|.
The command :command:`univention-configure-udm-authorization` reads every file
with the extension :file:`.policy` from this directory,
see :ref:`da-migration-guardian-generate`.

.. important::

   For the role ``udm:default-roles:domain-administrator``,
   univention-guardian grants all permissions on all UDM objects.
   Rules for this role in role definition files have no effect,
   so you can't restrict or extend the role.

.. _da-migration-guardian-generate:

Generate the policies
=====================

Instead of the role definition files,
univention-guardian evaluates its own policies.
You need to generate these policies from the role definition files
with the command :command:`univention-configure-udm-authorization`.
The command does the following:

* It reads every role definition file with the extension :file:`.policy`
  from :file:`/usr/share/univention-directory-manager-modules/policies/`.

* It reads the installed UDM modules
  to know which object types exist
  and which operations each of them supports.

* It writes the univention-guardian policies
  to :file:`/usr/share/univention-guardian-server/policies/udm/`
  and replaces the previous policies.

Afterwards, you can test the generated policies
with the test suites that come with UDM.
Because univention-guardian loads policies only when it starts,
restart it to use the new policies.

Run the commands in :numref:`da-migration-guardian-generate-listing`
on the |UCSPRIMARYDN| and on every |UCSBACKUPDN|.

.. code-block:: console
   :caption: Generate, test, and load the policies
   :name: da-migration-guardian-generate-listing

   $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization generate
   $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization test
   $ systemctl restart univention-guardian-server

Run these commands again every time you change a role definition file
or install additional UDM modules.
You don't need to run them again for new extended attributes.

.. _da-migration-guardian-switch:

Switch UDM to univention-guardian
=================================

To let UDM use univention-guardian instead of the local guardian,
run the commands in :numref:`da-migration-guardian-switch-listing`
on the |UCSPRIMARYDN| and on every |UCSBACKUPDN|.

.. code-block:: console
   :caption: Switch UDM to univention-guardian
   :name: da-migration-guardian-switch-listing

   $ ucr set directory/manager/delegative-administration/guardian=true
   $ systemctl restart univention-management-console-server univention-directory-manager-rest

.. TODO: register the UCR variable directory/manager/delegative-administration/guardian
   in the UCR variable descriptions and add it to :ref:`da-config-reference`.

.. _da-migration-guardian-verify:

Verify the migration
====================

#. Sign in to *UMC* as a user with a delegated role,
   for example an organizational unit administrator,
   and check that the user can manage the objects in their subtree
   and no objects outside of it.

#. Optionally, check the decisions of univention-guardian in its log.
   To log its decisions, univention-guardian needs the audit log.
   Enable the audit log
   as shown in :numref:`da-migration-guardian-verify-enable-listing`.

   .. code-block:: console
      :caption: Enable the audit log of univention-guardian
      :name: da-migration-guardian-verify-enable-listing

      $ ucr set guardian/cerbos/audit-logging/enabled=true
      $ systemctl restart univention-guardian-server

   Repeat the actions of the delegated user
   and view the log,
   as shown in :numref:`da-migration-guardian-verify-listing`.
   For every request from UDM,
   the log shows the principal, the object,
   the requested actions, and the decision.

   .. code-block:: console
      :caption: Show the decisions of univention-guardian
      :name: da-migration-guardian-verify-listing

      $ docker logs --since 10m cerbos

#. If you enabled the audit log in the previous step,
   disable it again,
   as shown in :numref:`da-migration-guardian-verify-disable-listing`.
   The audit log contains the properties of every object that UDM checks.

   .. code-block:: console
      :caption: Disable the audit log of univention-guardian
      :name: da-migration-guardian-verify-disable-listing

      $ ucr set guardian/cerbos/audit-logging/enabled=false
      $ systemctl restart univention-guardian-server

.. _da-migration-guardian-differences:

Differences from the local guardian
===================================

.. TODO: complete the list with the final behavior of the release.

* For users with a delegated role,
  searches start from the LDAP base.
  The search returns only objects within the scope of the role.

* For every role, univention-guardian denies actions
  that a UDM module doesn't support,
  for example removing the LDAP base.
