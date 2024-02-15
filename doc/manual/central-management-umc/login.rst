.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _central-management-umc-login:

Login
=====

UCS provides a central login page.
You can sign in to the |UCSWEB| with the credentials of the respective domain account.
On the portal at :samp:`https://{FQDN}/univention/portal/` you can use the following ways to sign in:

* Click the tile :guilabel:`Login` on the portal page

* Go to :menuselection:`Menu --> Login`

They open the login page as shown in :numref:`umc-login`.

.. _umc-login:

.. figure:: /images/umc_login.*
   :alt: UCS sign-in page
   :width: 440px

   UCS sign-in page

If a page in the management system, such as a UMC module, requires a login,
your browser redirects you to the central login page.

When you sign in at the local UCS system,
the browser session closes by default after 8 hours of inactivity.
You can change the timeout through the UCR variable :envvar:`umc/http/session/timeout`.
To get a new the session, the user must sign in again.

To sign out of the management system, click :guilabel:`Logout` in the user menu.

By installing a third-party application, such as :program:`privacyIDEA`, it's possible to extend
the |UCSWEB| authentication with a two-factor authentication (2FA).

Choose the right account
------------------------

To sign in, enter the *Username* and *Password* of the corresponding domain account in the login mask.

``Administrator``
   When you sign in with the ``Administrator`` account on a |UCSPRIMARYDN| or |UCSBACKUPDN|,
   the UCS management system shows the UMC modules
   for the administration and configuration of the local system,
   as well as,
   UMC modules for the administration of data in the LDAP directory.

   You specified the initial password for the ``Administrator`` account
   in the setup wizard during installation.
   The password corresponds to the initial password of the local ``root`` account.
   Use the ``Administrator`` account for the initial sign in at a newly installed |UCSPRIMARYDN|.

``root``
   In some cases, it might be necessary to sign in with the system's local ``root`` account.
   For more information, refer to :ref:`computers-rootaccount`.
   The ``root`` account only enables access to UMC modules for the administration and configuration of the local system.

Other user accounts
   When you sign in with another user account,
   the UCS management system shows the UMC modules approved for the user.
   For additional information on allowing further modules, refer to :ref:`delegated-administration`.

.. _central-management-umc-login-single-sign-on:

Single sign-on
--------------

By default, the login page for the portal has single sign-on deactivated.
The following sections describe how to activate single sign-on.
After a successful sign in,
the session is valid for all UCS systems of the domain,
as well as, for third party apps,
if the apps support web based single sign-on.

For sign-in through single sing-on,
the browser session closes for 8 hours of inactivity.
To get a new session, the user must sign in again.

It's possible to enforce the sign in on the local system
by clicking the link :guilabel:`Login without Single Sign On` on the login page,
as show in :numref:`umc-login-sso`.

.. _umc-login-sso:

.. figure:: /images/umc_login_sso.*
   :alt: UCS sign-in page for single sign-on
   :width: 440px

   UCS sign-in page for single sign-on

.. _central-management-umc-login-single-sign-on-saml:

SAML for single sign-on
~~~~~~~~~~~~~~~~~~~~~~~

You can activate single sign-on through SAML.
For more information, refer to :ref:`domain-saml`.

Activate
""""""""

To activate single sign-on through SAML, use the following steps:

#. Ensure that all users in your domain
   who want to use the portal and the UCS management system
   can reach :samp:`ucs-sso.{[Domain Name]}`.

#. Change the |UCSUCRV| :envvar:`portal/auth-mode` to ``saml`` with :option:`ucr set`.
   The default value was ``ucs``.

#. For the change to take effect, restart the portal server with the following command

   .. code-block:: console

      $ systemctl restart univention-portal-server.service

Update sign-in links
""""""""""""""""""""

Restarting the portal server automatically updates the *Login* link in the user menu.
You must manually update the portal tile.
The default portal has a preconfigured single sign-on login tile.
Use the portal edit mode to enable it.
To replace the *Login* tile with the single sign-on tile,
follow these steps:

#. In *Univention Management Console* open the UMC Module Portal:
   :menuselection:`Domain --> Portal`.

#. To activate the preconfigured sign in tile for SAML,
   edit the entry ``login-saml``,
   scroll down to the section *Advanced*
   and activate the checkbox :guilabel:`Advanced`.

#. To deactivate the default sign in tile,
   edit the entry ``login-ucs``,
   scroll down to the section *Advanced*
   and deactivate the checkbox :guilabel:`Advanced`.


