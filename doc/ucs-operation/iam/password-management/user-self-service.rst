.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _end-user-self-service:

*********************
End User Self Service
*********************

For general information about the *End User Self Service*,
see :external+uv-nubus-manual:ref:`nubus-user-management-self-service`
in :cite:t:`uv-nubus-manual`.
This section describes the *End User Self Service* configuration
specific to Nubus for UCS.

On this page, you find the following sections:

* :ref:`end-user-self-service-installation`
* :ref:`end-user-self-service-contact-information`
* :ref:`end-user-self-service-registration`
* :ref:`end-user-self-service-deregistration`

.. _end-user-self-service-installation:

Installation and activation
===========================

To enable users to manage their passwords on their own
through the *End User Self Service*,
you need to install the following UCS components through the *App Center*
to your UCS domain:

* :program:`Self Service Backend`
* :program:`Self Service`

:Endpoint: :samp:`https://{{fqdn-to-ucs-appliance}}/univention/selfservice/`

You can use the following UCR variables
to activate or deactivate individual features of the *End User Self Service* password management.
They also activate or deactivate the corresponding entries in the portal.
Additionally, you can adjust the portal entries manually,
because they're just normal portal entries.

.. envvar:: self-service/backend-server

   Defines the UCS system
   that has the :program:`Self Service Backend` app installed.

   :Default value: not defined
   :Type: string

.. envvar:: umc/self-service/passwordreset/backend/enabled

   Activates the *Password forgotten* functionality in the *Self Service*.

   You need to provide this setting on the Nubus for UCS node
   that you defined as :program:`Self Service Backend`
   through the UCR variable
   :envvar:`self-service/backend-server`,
   because the *End User Self Service* forwards requests for password reset
   to the configured backend.

   :Default value: ``true``
   :Type: boolean

.. envvar:: umc/self-service/protect-account/backend/enabled

   Activates the *Protect account* functionality in the *Self Service*.

   You need to provide this setting on the Nubus for UCS node
   that you defined as :program:`Self Service Backend`
   through the UCR variable
   :envvar:`self-service/backend-server`,
   because the *End User Self Service* forwards requests for account protection
   to the configured backend.

   :Default value: ``true``
   :Type: boolean

.. envvar:: umc/self-service/service-specific-passwords/backend/enabled

   Activates the service-specific passwords in the *Self Service*.

   Nubus supports only the RADIUS service.
   For more information,
   see :external+uv-ucs-manual:ref:`ip-config-radius-configuration-service-specific-password`.

   :Default value: ``true``
   :Type: boolean

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal-management`
      in :cite:t:`uv-nubus-manual`
      for information about how to edit portal entries.

.. _end-user-self-service-contact-information:

Contact information
===================

Users can view and update their own contact information through the *Self Service*.
Administrators control which attributes users can modify and which ones are read-only.

To configure the contact information in the *End User Self Service*,
use the following UCR variables:

.. envvar:: self-service/ldap_attributes

   This variable configures the *LDAP* attributes
   that users can modify on their own user account.
   You need to set the variable on the
   :term:`UCS Primary Directory Node` and the :term:`UCS Backup Directory Node`
   in your Nubus for UCS domain.
   On the Primary Directory Node,
   the UCR module generates and activates the ACL definition list
   in the directory service.

   :Default value: ``jpegPhoto,mail,telephoneNumber,roomNumber,departmentNumber,st,c,homePhone,mobile,homePostalAddress``
   :Type: List of strings, separated by commas

.. envvar:: self-service/udm_attributes

   Defines a comma-separated list of UDM attributes
   that the *Self Service* shows on the *Contact information* page
   where users can modify their user account.

   You need to set this UCR variable on all Nubus for UCS systems
   where you have installed the :program:`Self Service` app,
   and on the :term:`UCS Primary Directory Node`.

   :Default value: not defined
   :Type: List of strings, separated by commas

.. envvar:: self-service/udm_attributes/read-only

   Defines the UDM attributes as a comma-separated list of strings
   that the *Self Service* marks as read-only on the *Contact information*.
   The UCR variable
   :envvar:`self-service/udm_attributes`
   must include the UDM attributes.

   You need to set this UCR variable on all Nubus for UCS systems
   where you have installed the :program:`Self Service` app
   and on the :term:`UCS Primary Directory Node`.

   To ensure this variable works as intended,
   remove the *LDAP* attributes specified in the UCR variable
   :envvar:`self-service/ldap_attributes`
   that you want to be read-only.
   Otherwise, these *LDAP* attributes keep the corresponding *UDM* attributes writable.

   :Default value: not defined
   :Type: List of strings, separated by commas

.. envvar:: umc/self-service/profiledata/enabled

   Set the value of this variable to ``true`` on all involved Nubus for UCS systems
   to enable the profile data mechanism.

   :Default value: ``true``
   :Type: boolean

.. envvar:: umc/self-service/allow-authenticated-use

   This variable defines whether the *End User Self Service* requires username and password
   when users open and modify their own user profile
   if they have already signed in to the *Portal*.

   The :program:`Self Service` automatically sets the value to ``true``
   during app installation.
   ``true`` means that the *End User Self Service* uses an existing Portal session
   and doesn't ask for username and password if the user has already signed in.

   :Default value: ``true``
   :Type: boolean

The :envvar:`self-service/ldap_attributes` and :envvar:`self-service/udm_attributes`
variables must match each other.
You can fetch the attribute names and their mapping through the command in
:numref:`nubus-user-management-self-service-contact-info-listing`.

.. code-block:: console
   :caption: Fetch attribute names and mapping
   :name: nubus-user-management-self-service-contact-info-listing

   $ python3 -c 'from univention.admin.handlers.users.user import mapping; \
     print("\n".join( \
     map("{0[0]:>30s} {0[1][0]:<30s}".format, sorted(mapping._map.items()))) \
     )'

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-user-management-self-service-contact-info`
      in :cite:t:`uv-nubus-manual`
      for information about modifying user contact information.

.. _end-user-self-service-registration:

User registration
=================

The *End User Self Service* allows users to register themselves.
The registration creates a user account
that the user must verify through email.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-user-management-self-registration`
      in :cite:t:`uv-nubus-manual`
      for information about using the self-registration.

.. _end-user-self-service-registration-registration-form:

Registration form
-----------------

You can configure properties of the *Create an account* page
and the account creation itself
with the following Univention Configuration Registry (UCR) variables.

.. important::

   You must set these UCR variables
   on the Nubus for UCS system that provides :program:`Self Service Backend`
   as defined in the UCR variable :envvar:`self-service/backend-server`,
   because the self-service registration forwards requests to the Self Service backend.

.. envvar:: umc/self-service/account-registration/backend/enabled

   Activates the backend functionality for account creation.

   :Default value: ``false``
   :Type: boolean

.. envvar:: umc/self-service/account-registration/usertemplate

   Defines the DN of the user template
   that the *Self Service* uses to create an account
   through the *Create an account* page.

   If the variable has no value,
   the *Self Service* doesn't use a user template.

   For information about user account templates,
   see :external+uv-nubus-manual:ref:`nubus-user-templates`
   in :cite:t:`uv-nubus-manual`.

   :Default value: not defined
   :Type: string

.. envvar:: umc/self-service/account-registration/usercontainer

   Defines the DN of the container in the directory service
   where the *Self Service* stores the user account objects
   created through the *Create an account* page.

   If the variable has no value,
   the *Self Service* uses the configured default container for user account objects.

   :Default value: not defined
   :Type: string

.. envvar:: umc/self-service/account-registration/udm_attributes

   Defines a comma-separated list of UDM attributes
   that the *Self Service* shows on the *Create an account* page.

   :Default value: not defined
   :Type: List of strings, separated by commas

.. envvar:: umc/self-service/account-registration/udm_attributes/required

   Defines the UDM attributes as a comma-separated list of strings
   that the *Self Service* marks as required on the *Create an account* page.
   The UCR variable
   :envvar:`umc/self-service/account-registration/udm_attributes`
   must include the UDM attributes.

   :Default value: not defined
   :Type: List of strings, separated by commas

.. _end-user-self-service-registration-email-verification:

Email verification
------------------

When users register through the *Self Service*,
they receive a verification email with a token
to confirm their email address.
This section describes
how to configure the verification email and token properties.

You can configure properties of the *verification email*
and of the verification token
through the following Univention Configuration Registry variables.
For information about the verification process,
see :external+uv-nubus-manual:ref:`nubus-user-management-self-service-registration-verification-email`
in :cite:t:`uv-nubus-manual`.

.. important::

   You must set these UCR variables
   on the Nubus for UCS system that provides :program:`Self Service Backend`
   as defined in the UCR variable :envvar:`self-service/backend-server`,
   because the self-service registration forwards requests to the Self Service backend.

.. envvar:: umc/self-service/account-verification/email/webserver_address

   Defines the ``host`` part to use in the verification URL.
   The default value uses
   the fully qualified domain name of the :program:`Self Service Backend`
   as defined through the UCR variable
   :envvar:`self-service/backend-server`.

   :Default value: fully qualified domain name of the :program:`Self Service Backend`
   :Type: string

.. envvar:: umc/self-service/account-verification/email/sender_address

   Defines the sender address of the verification email.

   :Default value: :samp:`Account Verification Service <noreply@{FQDN}>`
   :Type: string

.. envvar:: umc/self-service/account-verification/email/server

   Defines the server name or IP address of the mail server to use.

   :Default value: ``localhost``
   :Type: string

.. envvar:: umc/self-service/account-verification/email/text_file

   Defines the path to a text file
   that the *Self Service* uses for the text body of the verification email.
   The text can contain the following strings.
   The *Self Service* substitutes them accordingly.

   ``{link}``
      URL to the *Self Service* page.

   ``{token}``
      The token string that the user can enter on the *Self Service* page
      to verify their email address.

   ``{tokenlink}``
      URL to the *Self Service* page
      that already includes the ``{token}``.

   ``{username}``
      The username of the user's account.

   :Default value: :file:`/usr/share/univention-self-service/email_bodies/verification_email_body.txt`
   :Type: string

.. envvar:: umc/self-service/account-verification/email/token_length

   Defines the number of characters
   that the *Self Service* uses for the verification token.

   :Default value: ``64``
   :Type: unsigned integer

.. _end-user-self-service-registration-account-activation:

Account activation
------------------

When the user clicks the verification link from the email,
the web browser shows the *Account verification* page of the *Self Service*.
For information about how to verify the registered user account,
see :external+uv-nubus-manual:ref:`nubus-user-management-self-service-registration-account-verification`.

This section provides information about how to configure the account verification.

.. important::

   You must set these UCR variables
   on the Nubus for UCS system that provides :program:`Self Service Backend`
   as defined in the UCR variable :envvar:`self-service/backend-server`,
   because the self-service registration forwards requests to the Self Service backend.

.. envvar:: umc/self-service/account-verification/backend/enabled

   Activates the *Account verification* functionality in the *Self Service*.

   :Default value: ``false``
   :Type: boolean

Handle sign-in for user accounts with an unverified email address
   You can configure single sign-on
   to require self-registered users to first verify their email address.

   Use the UCR variable
   :external+uv-keycloak-app:envvar:`ucs/self/registration/check_email_verification`.

User notification for user accounts with an unverified email address
   You can configure the user notification on the single sign-on page
   for self-registered user accounts with an unverified email address.
   Use the following UCR variables:

   * :external+uv-keycloak-app:envvar:`keycloak/login/messages/en/accountNotVerifiedMsg`
   * :external+uv-keycloak-app:envvar:`keycloak/login/messages/de/accountNotVerifiedMsg`

Since UCS 5.2, the :program:`Keycloak` app is the default identity provider.
For information about Keycloak settings,
see :external+uv-keycloak-app:ref:`app-settings` in the :cite:t:`ucs-keycloak-doc`.

.. _end-user-self-service-deregistration:

User deregistration
===================

The :program:`Self Service` allows users
to request the deletion of their user account.

.. _end-user-self-service-deregistration-request:

Deregistration request
----------------------

If a user requests to delete their account,
Nubus doesn't delete the user account directly,
but deactivates it.
If the user has a ``PasswordRecoveryEmail`` defined,
Nubus sends a notification email.
In addition,
Nubus sets the following attributes of the user account:

* ``DeregisteredThroughSelfService`` to ``TRUE``
* ``DeregistrationTimestamp`` to the current time in the `GeneralizedTime LDAP syntax <ldap-generalized-time_>`_.

Use the following UCR variables to configure user self-deregistration.

.. envvar:: umc/self-service/account-deregistration/enabled

   Activates the *Delete my account* button on the *Your profile* page
   of the *Self Service*.

   :Default value: not defined
   :Type: boolean

.. envvar:: umc/self-service/account-deregistration/email/sender_address

   Defines the sender address of the notification email
   about a user account deletion request.

   :Default value: :samp:`Password Reset Service <noreply@{FQDN}>`
   :Type: string

.. envvar:: umc/self-service/account-deregistration/email/server

   Defines the server name as fully qualified domain name
   or IP address of the mail server
   for sending the notification email about a user account deletion request.

   :Default value: not defined
   :Type: string

.. envvar:: umc/self-service/account-deregistration/email/text_file

   Defines the path to a text file
   that the *Self Service* uses for the text body of the notification email.
   The text can contain the following strings.
   The *Self Service* substitutes them accordingly.

   ``{username}``
      The username of the user's account.

   :Default value: :file:`/usr/share/univention-self-service/email_bodies/deregistration_notification_email_body.txt`
   :Type: string

.. _end-user-self-service-deregistration-cleanup:

Account cleanup
---------------

The *Self Service* provides a script at
:file:`/usr/share/univention-self-service/delete_deregistered_accounts.py`
that you can use
to delete all ``users/user`` objects
that have
the ``DeregisteredThroughSelfService`` attribute set to ``TRUE``
and whose ``DeregistrationTimestamp`` attribute is older than a specified time.

.. _end-user-self-service-deregistration-manual-deletion:

Manually delete deregistered user accounts
   The command in :numref:`end-user-self-service-deregistration-delete-listing`
   deletes user accounts whose ``DeregistrationTimestamp`` is older than 5 days and 2 hours.

   .. code-block:: console
      :caption: Example for deleting deregistered and deactivated user accounts
      :name: end-user-self-service-deregistration-delete-listing

      $ /usr/share/univention-self-service/delete_deregistered_accounts.py \
        --timedelta-days 5 \
        --timedelta-hours 2

.. _end-user-self-service-deregistration-script-arguments:

Script arguments
   For the possible arguments of the script,
   see :numref:`end-user-self-service-deregistration-script-arguments-listing`.

   .. code-block::
      :caption: Available arguments for :file:`delete_deregistered_accounts.py`
      :name: end-user-self-service-deregistration-script-arguments-listing

      $ /usr/share/univention-self-service/delete_deregistered_accounts.py --help

.. _end-user-self-service-deregistration-scheduled-deletion:

Scheduled deletion of deregistered user accounts
   You can schedule the script to run regularly.
   Create a cron job through a UCR variable,
   as shown in :numref:`end-user-self-service-deregistration-schedule-listing`.

   .. code-block:: console
      :caption: Schedule deletion of deregistered user accounts
      :name: end-user-self-service-deregistration-schedule-listing

      $ ucr set cron/delete_deregistered_accounts/command=\
      /usr/share/univention-self-service/delete_deregistered_accounts.py\
      ' --timedelta-days 30'\
        cron/delete_deregistered_accounts/time='00 06 * * *'  # daily at 06:00

For more information about how to set cron jobs through UCR variables,
see
:external+uv-ucs-manual:ref:`computers-defining-cron-jobs-in-univention-configuration-registry`.

.. _ldap-generalized-time: https://ldapwiki.com/wiki/Wiki.jsp?page=GeneralizedTime
