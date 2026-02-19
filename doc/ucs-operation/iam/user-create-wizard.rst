.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _iam-user-create-wizard:

User creation wizard
====================

For quick user account creation,
functional administrators can use the user creation wizard.
For information about the wizard,
see :external+uv-nubus-manual:ref:`nubus-user-management-create-wizard`
in :cite:t:`uv-nubus-manual`.
This page addresses administrators on configuring the user creation wizard,
which requires changes to the system.

.. _iam-user-create-wizard-require-primary-email:

Require primary email address in user creation wizard
-----------------------------------------------------

When activated with the value ``true``,
the *User creation wizard* requires functional administrators
to provide a primary email address for a user account.
To activate this requirement,
apply the following steps
on the :term:`Primary Directory Node` of your Nubus for UCS installation:

#. Set the UCR variable
   :envvar:`directory/manager/web/modules/users/user/properties/mailPrimaryAddress/required`
   to the value ``true``.

#. To apply the changes,
   you need to restart the *UMC Server*
   as described in :ref:`restart-umc-server`.

.. _iam-user-create-wizard-deactivate:

Deactivate user creation wizard
-------------------------------

To deactivate the user creation wizard
in the *Users* management module
in Nubus for UCS,
use the following steps:

#. Set the UCR variable
   :envvar:`directory/manager/web/modules/users/user/wizard/disabled`
   to the value ``true``.

#. To apply the changes,
   you need to restart the *UMC Server*
   as described in :ref:`restart-umc-server`.

.. _iam-user-create-wizard-account-properties:

Control account properties for user setup
-----------------------------------------

The user creation wizard provides the following additional properties
to control user account setup.

*Invite user via e-mail. Password will be set by the user*
   If you activate this checkbox,
   the wizard replaces the password input fields
   with an input field where you enter an email address.
   Upon user creation,
   the *Management UI* sends an invitation email containing a link
   where the user can set their password.

   The wizard also deactivates the properties
   *User has to change password on next login*
   and *Override password check*,
   which remain visible but functional administrators can't change them.
   The link in the invitation email directs the user to the *User Self Service*
   where they must define a password
   that meets the defined password quality rules.

   * :envvar:`directory/manager/web/modules/users/user/wizard/property/invite/visible`
   * :envvar:`directory/manager/web/modules/users/user/wizard/property/invite/default`

*User has to change password on next login*
   If you activate this checkbox,
   the user must change their password on the next sign-in.

   * :envvar:`directory/manager/web/modules/users/user/wizard/property/pwdChangeNextLogin/visible`
   * :envvar:`directory/manager/web/modules/users/user/wizard/property/pwdChangeNextLogin/default`

*Override password check*
   If you activate this checkbox,
   the *Directory Manager* skips
   the password quality and minimum password length checks.

   * :envvar:`directory/manager/web/modules/users/user/wizard/property/overridePWLength/visible`
   * :envvar:`directory/manager/web/modules/users/user/wizard/property/overridePWLength/default`

*Account disabled*
   If you activate this checkbox,
   the *Directory Manager* creates the user account
   in a deactivated state
   that prevents the user from signing in.

   You can use this property to prepare a user account in advance
   and activate it when ready.

   * :envvar:`directory/manager/web/modules/users/user/wizard/property/disabled/visible`
   * :envvar:`directory/manager/web/modules/users/user/wizard/property/disabled/default`

To configure whether the wizard shows these properties,
and define the properties' default values,
use the following steps:

#. Configure the UCR variables.
   Limit the configuration to those properties that you actually need.
   Each property has the following attributes:

   ``visible``
      Set the attribute to ``true`` to show the checkbox for the property.
      When unset or set to ``false``,
      the *Management UI* hides the checkbox.
      Possible values are ``true`` and ``false``.

   ``default``
      Sets the default value for the property.
      Defaults to ``false``.
      Possible values are ``true`` and ``false``.

   Example
      To activate the checkbox to invite users through email,
      set the following UCR variables:

      * :envvar:`directory/manager/web/modules/users/user/wizard/property/invite/visible` to
        ``true``
      * :envvar:`directory/manager/web/modules/users/user/wizard/property/invite/default` to
        ``false``

#. To apply the changes,
   you need to restart the *UMC Server*
   as described in :ref:`restart-umc-server`.

.. _restart-umc-server:

Restart the UMC server
----------------------

.. TODO: Move this section to a place about service restarts.

For some configuration changes to take effect,
you must restart the UMC server.
To restart the UMC server,
use the command in :numref:`restart-umc-server-listing`.

.. code-block:: console
   :caption: Restart the UMC Server on Primary Directory Node
   :name: restart-umc-server-listing

   $ service univention-management-console-server restart

.. caution::

   *UMC Server* instances generate and maintain the user session.
   Only the generating instance knows about the user session.
   Any requests in the context of the user session need to use that *UMC Server* instance.

   However, if you restart individual *UMC Server* instances
   users whose session belongs to the affected *UMC Server* instances
   lose their user session.
