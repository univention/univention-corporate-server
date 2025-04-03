.. SPDX-FileCopyrightText: 2025 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _da-setup-test-env:

****************************
Setup of an test environment
****************************

Univention released the preview for the delegative administration as a normal errata update for UCS 5.2-1.
However, you as an administrator need to explicitly activate the feature
and perform some additional steps to test its functionality.

.. _da-setup-test-env-preparation:

Preparation
===========

To prepare a UCS 5.2-1 test environment for using delegative administration,
use the following steps:

#. Set up a new UCS 5.2-1 |UCSPRIMARYDN| test system
   and upgrade to the latest errata updates.

#. Assign the role ``umc:udm:domainadmin`` as ``guardianMemberRoles`` to the group ``Domain Admins``.
   ``umc:udm:domainadmin`` is a default role to allow access to the directory for ``Administrators``.
   Run the command in :numref:`da-setup-test-env-preparation-add-role-listing` on the |UCSPRIMARYDN|.
   For information about roles, see :term:`Roles`.

   .. code-block:: console
      :caption: Assign ``umc:udm:domainadmin`` as default role for the Domain Admins group
      :name: da-setup-test-env-preparation-add-role-listing

      $ udm groups/group modify \
         --dn "cn=Domain Admins,cn=groups,$(ucr get ldap/base)" \
         --append guardianMemberRoles="umc:udm:domainadmin"

#. By default,
   only members of the user group ``Domain Admins`` can see and use the user and group modules in UMC.
   To properly test the delegative administration feature,
   you need to assign the right
   to see and use the user and group module in UMC
   to every user object.
   Run the command in :numref:`da-setup-test-env-preparation-assign-rights-listing` on the |UCSPRIMARYDN|.

   .. code-block:: console
      :caption: Assign the right to see the users and group modules in UMC to every user object
      :name: da-setup-test-env-preparation-assign-rights-listing

      $ udm policies/umc modify \
          --dn "cn=default-umc-users,cn=UMC,cn=policies,$(ucr get ldap/base)" \
          --append allow="cn=udm-groups,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
          --append allow="cn=udm-users,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)" \
          --append allow="cn=udm-syntax,cn=operations,cn=UMC,cn=univention,$(ucr get ldap/base)"

.. _da-setup-test-env-activate:

Activate delegative administration
==================================

To activate delegative administration on every UCS system in your test environment,
you need to run the commands in :numref:`da-setup-test-env-activate-listing`
on every system.

.. code-block:: console
   :caption: Activate delegative administration on a UCS system
   :name: da-setup-test-env-activate-listing

   $ ucr set umc/udm/delegation='true'
   $ service univention-management-console-server restart

.. _da-setup-test-env-test:

Test delegative administration
==============================

To test delegative administration, use the following steps:

#. Sign in as ``Administrator`` to the UMC.

   You notice no difference,
   because the user ``Administrator`` is in the ``Domain Admins`` user group.
   Due to this group membership,
   you can still see all user objects or group objects
   and are able to create and modify every object.

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

#. Sign in to the UMC with the ``test1`` user account
   that you just created.
   Open the *Users* module.
   The result list is empty,
   because the user object ``test1`` has no permission to read objects from the LDAP directory.

.. _da-setup-test-env-ouadmin:

Preparation for testing the ``ouadmin`` default role
====================================================

A more interesting example is the role ``ouadmin``.
This role gives the user the ability to manage a position of the directory.
User objects with this role have the following permissions:

* They can see, create, modify, and delete user objects in their organizational unit
  and below in the directory structure.

* They can see user group objects in the container :samp:`cn=groups,{LDAP_BASE}`.

* They can read ``mail/domain`` objects in the container :samp:`cn=domain,cn=mail,{LDAP_BASE}`.

* They can read ``policies/desktop``, ``policies/pwhistory`` and ``policies/umc`` object in any other position.

* They can't see or modify user objects or group objects in any other position.

* They can't modify the attribute ``guardianRoles`` of users.
  This role can't manage roles.

To test this role, you need to prepare your test environment.
The following shell script creates and configures 10 organizational units,
one user object with the role ``ouadmin`` for each organizational unit
and 10 user objects within each organizational unit.
Run the commands in :numref:`da-setup-test-env-ouadmin-listing` on the |UCSPRIMARYDN|.

.. code-block:: console
   :caption: Create 10 organizational units with 10 user objects each
   :name: da-setup-test-env-ouadmin-listing

   for i in $(seq 1 10); do
     # create some structure and a ouadmin user
     ou="ou${i}"
     udm container/ou create \
       --set name="$ou" \
       --set groupPath=1 \
       --set userPath=1
     udm container/cn create \
       --position="ou=$ou,$(ucr get ldap/base)" \
       --set name=users \
       --set userPath=1
     udm container/cn create \
       --position="ou=$ou,$(ucr get ldap/base)" \
       --set name=groups \
       --set groupPath=1
     udm users/user create \
       --position="cn=users,$(ucr get ldap/base)" \
       --set username="${ou}-admin" \
       --set password=univention \
       --set lastname="${ou}-admin" \
       --append guardianRoles="umc:udm:ouadmin&umc:udm:ou=${ou}"
     # create some users
     for j in $(seq 1 10); do
       username="user${j}-${ou}"
       udm users/user create \
         --position="cn=users,ou=${ou},$(ucr get ldap/base)" \
         --set username="$username" \
         --set password=univention \
         --set lastname="$username"
     done
   done

Now you can sign in to UMC with the ``ou1-admin`` user, the password ``univention``,
and open the *Users* module.
You see only the users of the organizational unit ``ou1``, nothing else.

You can also manually add the role ``umc:udm:ouadmin&umc:udm:ou=ou2`` to the ``guardianRoles`` property of the user ``ou1-admin``.
The user then has ``ouadmin`` rights for two the organizational units ``ou=ou1`` and ``ou=ou2``.

.. _da-setup-test-env-deactivate:

Deactivate delegative administration
====================================

To deactivate delegative administration,
you need to run the commands in :numref:`da-setup-test-env-deactivate-listing`
on every UCS system in your test environment.

.. code-block:: console
   :caption: Deactivate delegative administration on one UCS system
   :name: da-setup-test-env-deactivate-listing

   $ ucr unset umc/udm/delegation
   $ service univention-management-console-server restart
