.. SPDX-FileCopyrightText: 2025-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-setup-test-env:

*************************
Set up a test environment
*************************

Univention released the preview for the delegative administration as an errata update for UCS 5.3-2.
To test its functionality,
you as an administrator need to explicitly activate the feature
and run some additional steps:

#. :ref:`da-setup-test-env-preparation`
#. :ref:`da-setup-test-env-activate`
#. :ref:`da-setup-test-env-test`
#. :ref:`da-setup-test-env-ouadmin`
#. :ref:`da-setup-test-env-deactivate`

.. _da-setup-test-env-preparation:

Preparation
===========

To prepare a UCS 5.3-2 test environment for using delegative administration,
use the following steps:

#. Set up a dedicated UCS 5.3-2 |UCSPRIMARYDN| test system
   and upgrade to the latest errata level.

#. To allow the ``Administrator`` user access to the directory,
   you need to assign the default role ``udm:default-roles:domain-administrator`` as ``guardianMemberRoles``
   to the user group ``Domain Admins``.
   Run the command in :numref:`da-setup-test-env-preparation-add-role-listing` on the |UCSPRIMARYDN|.
   For information about roles, see :term:`Role`.

   .. code-block:: console
      :caption: Assign ``udm:default-roles:domain-administrator`` as default role for the ``Domain Admins`` group
      :name: da-setup-test-env-preparation-add-role-listing

      $ udm groups/group modify \
         --dn "cn=Domain Admins,cn=groups,$(ucr get ldap/base)" \
         --append guardianMemberRoles="udm:default-roles:domain-administrator"

#. Create default roles and permissions for the authorization engine.
   Run the commands in :numref:`da-setup-test-env-preparation-default-roles` on the |UCSPRIMARYDN|.

   .. code-block:: console
      :caption: Create default roles and permissions
      :name: da-setup-test-env-preparation-default-roles

      $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization \
          --store-local prune
      $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization \
          --store-local create-permissions
      $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization \
          --store-local create-default-roles

#. If you add extended attributes or UDM modules,
   after the initial setup you need to update the internal permissions.
   Run the command in :numref:`da-setup-test-env-preparation-update-permissions` on the |UCSPRIMARYDN|.

   .. code-block:: console
      :caption: Update permissions
      :name: da-setup-test-env-preparation-update-permissions

      $ /usr/share/univention-directory-manager-tools/univention-configure-udm-authorization \
          --store-local create-permissions

.. _da-setup-test-env-activate:

Activate delegative administration
==================================

You have to activate delegative administration
separately for the components *UMC* and *UDM HTTP REST API*.
This section covers the necessary steps:

#. :ref:`da-setup-test-env-activate-umc`
#. :ref:`da-setup-test-env-activate-udm-http-rest`

.. _da-setup-test-env-activate-umc:

UMC
---

To activate delegative administration for the *UMC* service on every UCS system in your test environment,
you need to run the commands in :numref:`da-setup-test-env-activate-listing-umc`
on every system.

.. code-block:: console
   :caption: Activate delegative administration on a UCS system
   :name: da-setup-test-env-activate-listing-umc

   $ ucr set directory/manager/web/delegative-administration/enabled=true
   $ systemctl restart univention-management-console-server

Additionally, you have to configure authorization for the *UMC* service, see :ref:`da-limits`.

By default, only members of the user group ``Domain Admins`` can see and use the user and group modules in *UMC*.
To properly test the delegative administration feature,
you need to create a policy that allows all UMC modules.
You can assign this policy to user objects to allow access to UMC modules.
Run the command in :numref:`da-setup-test-env-preparation-assign-rights-listing` on the |UCSPRIMARYDN|.

.. code-block:: console
   :caption: Create UMC policy for access to UMC modules
   :name: da-setup-test-env-preparation-assign-rights-listing

   $ udm policies/umc create \
        --position "cn=UMC,cn=policies,$(ucr get ldap/base)" \
        --set name="test-policy" \
        --append allow="cn=udm-all,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)"

.. _da-setup-test-env-activate-udm-http-rest:

UDM HTTP REST API
-----------------

To activate delegative administration for the *UDM HTTP REST API* service on every UCS system in your test environment,
you need to run the commands in :numref:`da-setup-test-env-activate-listing-udm-rest`
on every system.

.. code-block:: console
   :caption: Activate delegative administration on a UCS system
   :name: da-setup-test-env-activate-listing-udm-rest

   $ ucr set directory/manager/rest/delegative-administration/enabled=true
   $ systemctl restart univention-directory-manager-rest


Additionally, you have to configure authorization for the UDM HTTP REST API service, see :ref:`da-limits`.

Create a group and allow the *UDM HTTP REST API* service for every member of this group on the |UCSPRIMARYDN|.
Run the commands in :numref:`da-setup-test-env-preparation-udm-rest-authz`.
Then, add every user object to this group that needs access to the *UDM HTTP REST API* service.

.. code-block:: console
   :caption: UDM REST authorization setup
   :name: da-setup-test-env-preparation-udm-rest-authz

   $ udm groups/group create \
       --set name="test-rest-api-access" \
       --position="cn=groups,$(ucr get ldap/base)"
   $ ucr set directory/manager/rest/authorized-groups/test-rest-api-access="cn=test-rest_api-access,cn=groups,$(ucr get ldap/base)"


.. _da-setup-test-env-test:

Test delegative administration
==============================

To test delegative administration, use the following steps:

#. Sign in as ``Administrator`` to the *UMC*.

   You notice no difference,
   because the user ``Administrator`` has the role ``udm:default-roles:domain-administrator``.
   This role allows users to perform every operation to every object in the *Directory Service*.
   The user group ``Domain Admins`` has the role assigned and
   the user object ``Administrator`` is member in the user group ``Domain Admins``.
   Remember step two in :ref:`da-setup-test-env-preparation`.

#. Create a test user account without a role.
   Use the command in :numref:`da-setup-test-env-test-listing`.

   .. code-block:: console
      :caption: Create user object without a role
      :name: da-setup-test-env-test-listing

      $ udm users/user create \
         --position="cn=users,$(ucr get ldap/base)" \
         --set username=test1 \
         --set password=univention \
         --set lastname=test

#. To test with the created user object, open a private browser window or sign out.

#. Sign in to the *UMC* with the ``test1`` user account
   that you just created.
   Open the *Users* module.
   The result list is empty,
   because the user object ``test1`` has no permission to read objects from the LDAP directory.

.. _da-setup-test-env-ouadmin:

Preparation for testing the default role for OUs
================================================

A more interesting example is the role ``udm:default-roles:organizational-unit-admin``.
This role gives user accounts the ability to manage a position in the *Directory Service*.
User objects with this role have the following permissions:

* They can see, create, modify, and delete user account and group objects in their organizational unit
  and below in the tree of the *Directory Service*.

* They can read the LDAP base object ``container/dc``.

* They can read ``mail/domain`` objects in the container :samp:`cn=domain,cn=mail,{LDAP_BASE}`.

* They can read ``policies/desktop``, ``policies/pwhistory``, and ``policies/umc`` objects in any other position.

* They can't see or modify user objects or group objects in any other position.

* They can't modify the attribute ``guardianRoles`` of users.
  This role can't manage roles.

The following steps show how you can test this role.

#. To test this role, you need to prepare your test environment.
   The shell script in
   :numref:`da-setup-test-env-ouadmin-listing`
   creates and configures ten organizational units,
   one user object with the role ``udm:default-roles:organizational-unit-admin`` for each organizational unit,
   and ten user objects within each organizational unit.
   Run the commands in :numref:`da-setup-test-env-ouadmin-listing` on the |UCSPRIMARYDN|.

   .. code-block:: bash
      :caption: Create ten organizational units with ten user objects each
      :name: da-setup-test-env-ouadmin-listing

      umc_policy="cn=test-policy,cn=UMC,cn=policies,$(ucr get ldap/base)"
      for i in $(seq 1 10); do
        # create some structure and a organizational-unit-admin user
        ou="ou${i}"
        udm container/ou create \
          --set name="$ou"
        udm container/cn create \
          --position="ou=$ou,$(ucr get ldap/base)" \
          --set name=users \
          --set userPath=1
        udm container/cn create \
          --position="ou=$ou,$(ucr get ldap/base)" \
          --set name=groups \
          --set groupPath=1
        # organizational unit admin
        udm users/user create \
          --position="cn=users,$(ucr get ldap/base)" \
          --policy-reference="$umc_policy" \
          --set username="${ou}-admin" \
          --set password=univention \
          --set lastname="${ou}-admin" \
          --append guardianRoles="udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=${ou},$(ucr get ldap/base)"
        # create some users
        for j in $(seq 1 10); do
          username="user${j}-${ou}"
          udm users/user create \
            --position="cn=users,ou=${ou},$(ucr get ldap/base)" \
            --policy-reference="$umc_policy" \
            --set username="$username" \
            --set password=univention \
            --set lastname="$username"
        done
        # primary group for each organizational unit
        udm groups/group create \
          --position="cn=groups,ou=$ou,$(ucr get ldap/base)" \
          --set name="$ou-users"
        # set ou primary group as default primary group for users in this
        # organizational unit
        udm container/ou modify \
          --dn "ou=$ou,$(ucr get ldap/base)" \
          --append-option group-settings \
          --set defaultGroup="cn=$ou-users,cn=groups,ou=$ou,$(ucr get ldap/base)"
      done

#. Sign in to *UMC* with the ``ou1-admin`` user, the password ``univention``, and open the *Users* module.
   You only see the users of the organizational unit ``ou1``, nothing else.

   You can also manually add the role
   ``udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou2,${ldap_base}``
   to the ``guardianRoles`` property of the user ``ou1-admin``.
   The user then has ``organizational-unit-admin`` permissions for two the organizational units ``ou=ou1`` and ``ou=ou2``.

.. _da-setup-test-env-deactivate:

Deactivate delegative administration
====================================

To deactivate delegative administration,
you need to run the commands in :numref:`da-setup-test-env-deactivate-listing`
on every UCS system in your test environment.

.. code-block:: console
   :caption: Deactivate delegative administration on one UCS system
   :name: da-setup-test-env-deactivate-listing

   $ ucr unset \
     directory/manager/web/delegative-administration/enabled \
     directory/manager/rest/delegative-administration/enabled
   $ systemctl restart univention-management-console-server \
     univention-directory-manager-rest
