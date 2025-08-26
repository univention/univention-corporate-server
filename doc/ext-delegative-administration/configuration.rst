.. SPDX-FileCopyrightText: 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-config-reference:

*********************
Configuration options
*********************

This section describes configuration files and options
for the delegative administration of the *Directory Service* through UDM.

Default roles
=============

The following file defines the default UDM roles and their rights.

:file:`/usr/share/univention-directory-manager-modules/udm-default-authorization-roles.policy`
   Contains the default roles, like ``udm:default-roles:domain-administrator`` or ``udm:default-roles:organizational-unit-admin``.

   .. important::

      Don't change this file.
      UCS updates overwrite it.

Custom roles
============

You can define your own roles in the configuration file :file:`/etc/custom-udm-roles.policy`.
The file doesn't exist by default.
However, you can create this file and add custom role definitions.
The structure of the file may change at any time.
If you have multiple servers in your test environment,
you have to manually keep this file in synchronization between servers.
For details about the format of this file, see :ref:`da-concepts-role-definition`.

After creating or modifying this file,
you have to run the command
:numref:`da-concepts-custom-roles-activate`
to update the rules.
You can use the roles
that you defined in this file,
as value for the ``guardianRoles`` property of user objects.

.. code-block::
   :caption: Activate custom role and rules
   :name: da-concepts-custom-roles-activate

   $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization \
       --store-local create-roles \
       --config /etc/udm-roles.policy

Options
=======

The following references show the available settings for delegative administration:

.. envvar:: directory/manager/web/delegative-administration/enabled

   Activate or deactivate delegative administration for UMC.

   Possible values:
      ``true`` or ``false``.

.. envvar:: directory/manager/rest/delegative-administration/enabled

   Activate or deactivate delegative administration for UDM REST API.

   Possible values:
      ``true`` or ``false``.
