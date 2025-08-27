.. SPDX-FileCopyrightText: 2024 - 2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _end-user-self-service:

*********************
End User Self Service
*********************

This section describes the UCS appliance specific configuration
for the *End User Self Service*.
For general information about it,
see :external+uv-nubus-manual:ref:`nubus-user-management-self-service`.

.. _end-user-self-service-installation:

Installation and activation
===========================

To enable users to manage their password on their own
through the *End User Self Service*,
you need to install the following UCS components through the *App Center*
to your domain of UCS appliances:

* :program:`Self Service Backend`
* :program:`Self Service`

:Endpoint: :samp:`https://{{fqdn-to-ucs-appliance}}/univention/selfservice/`

You can use the following UCR variables
to activate or deactivate individual features of the *End User Self Service* password management.
They also activate or deactivate the corresponding entries in the portal.
Additionally, you can also adjust the portal entries manually,
because, in fact, they're just normal portal entries.

.. envvar:: umc/self-service/passwordreset/backend/enabled

   Activates or deactivates the backend of the *Password forgotten* page.

   You need to provide this setting on the UCS appliance system
   that you defined as :program:`Self Service backend`
   through the UCR variable
   :external+uv-ucs-manual:envvar:`self-service/backend-server`,
   because the *End User Self Service* forwards requests for password reset
   to the configured backend.

.. envvar:: umc/self-service/protect-account/backend/enabled

   Activates or deactivates the backend of the *Protect account* page.

   You need to provide this setting on the UCS appliance system
   that you defined as :program:`Self Service backend`
   through the UCR variable
   :external+uv-ucs-manual:envvar:`self-service/backend-server`,
   because the *End User Self Service* forwards requests for password reset
   to the configured backend.

.. envvar:: umc/self-service/service-specific-passwords/backend/enabled

   Activates or deactivates the backend for service specific passwords.

   Nubus only supports the service RADIUS.
   For more information,
   see :external+uv-ucs-manual:ref:`ip-config-radius-configuration-service-specific-password`.

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-portal-management`
      for information about how to edit portal entries.

.. _end-user-self-service-contact-information:

Contact information
===================

.. TODO: Add introduction to this section

To configure the contact information in the *End User Self Service*,
use the following UCR variables:

.. envvar:: self-service/ldap_attributes

   This variable configures the *LDAP* attributes
   that a user can modify at its own user account.
   You need to set the variable on the UCS Primary Directory Node and the UCS Backup Directory
   nodes on your UCS appliances systems.
   Separate the attribute names by comma.

.. envvar:: self-service/udm_attributes

   This variable configures the *UDM* attributes
   that a user can modify.
   You need to set this UCR variable on all UCS appliance hosts,
   where you have installed the :program:`Self Service` app
   and on the UCS Primary Directory node.
   Separate the UDM attribute names by comma.

.. envvar:: self-service/udm_attributes/read-only

   This variable sets *UDM* attributes to read-only
   that you specified in the UCR variable :envvar:`self-service/udm_attributes`.
   You need to set this UCR variable on all UCS appliance hosts,
   where you have installed the :program:`Self Service` app
   and on the UCS Primary Directory node.
   Separate the UDM attribute names by comma.

   To prevent this variable's intended behavior from being prohibited,
   remove the *LDAP* attributes specified in the UCR variable
   :envvar:`self-service/ldap_attributes`
   that you want to be read-only.
   Otherwise, these *LDAP* attributes keep the corresponding *UDM* attributes writable.

.. envvar:: umc/self-service/profiledata/enabled

   Set the value of this variable to ``true`` on all involved UCS appliance systems
   to enable the mechanism.

.. envvar:: umc/self-service/allow-authenticated-use

   This variable defines whether the *End User Self Service* requires username and password
   when users open and modify their own user profile
   if they already signed in to the *Portal*.

   The :program:`Self Service` automatically sets the value to ``true``
   during app installation.
   ``true`` means that the *End User Self Service* uses an existing Portal session
   and doesn't ask for username and password, if the user already signed in.

The :envvar:`self-service/ldap_attributes` and :envvar:`self-service/udm_attributes` variables must match each other.
You can fetch the attribute names and their mapping through the command in
:numref:`nubus-user-management-self-service-contact-info-listing`.

.. code-block:: console
   :caption: Fetch attribute names and mapping
   :name: nubus-user-management-self-service-contact-info-listing

   $ python3 -c 'from univention.admin.handlers.users.user import mapping;\
     print("\n".join( \
     map("{0[0]:>30s} {0[1][0]:<30s}".format, sorted(mapping._map.items()))) \
     )'

.. _end-user-self-service-registration:

Self registration
=================

The *End User Self Service* allows users to register themselves.
The registration creates a user account
that the user must verify through email.

User accounts that users created through the *End User Self Service*
have the ``RegisteredThroughSelfService`` attribute set to the value ``TRUE``
and the ``PasswordRecoveryEmailVerified`` attribute set to the value ``FALSE``.
After the user has verified their email address and completed the registration procedure,
the ``PasswordRecoveryEmailVerified`` has the value ``TRUE``.

.. _end-user-self-service-registration-create-account:

Create account
--------------

:numref:`nubus-user-management-self-service-registration-create-account-figure`
shows the *Create an account* dialog.

.. _nubus-user-management-self-service-registration-create-account-figure:

.. figure:: /images/users_self-service_registration.*
   :alt: Account registration

   Account registration

Aspects about the *Create an account* page and the account creation
itself can be configured with the following Univention Configuration Registry variables. These
Univention Configuration Registry variables
have to be set on the systems that is defined as :program:`Self Service Backend`
via the Univention Configuration Registry variable :envvar:`self-service/backend-server`, since
requests regarding these variables are forwarded to the Self Service
backend.

.. envvar:: umc/self-service/account-registration/backend/enabled

   With this variable the account registration can be disabled/enabled.

.. envvar:: umc/self-service/account-registration/usertemplate

   With this variable a :external+uv-nubus-manual:ref:`nubus-user-templates` can be specified
   that will be used for the creation of self registered accounts.

.. envvar:: umc/self-service/account-registration/usercontainer

   With this variable a container can be specified under which the self
   registered users are created.

.. envvar:: umc/self-service/account-registration/udm_attributes

   This variable configures which UDM attributes of a user account are shown on
   the *Create an account* page of the Self Service. The names of the UDM
   attributes must be provided as a comma separated list.

.. envvar:: umc/self-service/account-registration/udm_attributes/required

   This variable configures which of the UDM attributes set via the Univention Configuration
   Registry variable
   :envvar:`umc/self-service/account-registration/udm_attributes` are required
   for the user to provide. The names of the UDM attributes must be provided as
   a comma separated list.

.. _end-user-self-service-registration-verification-email:

Verification email
------------------

After a user has clicked on :guilabel:`Create account`, they
will see a message that an email for the account verification has been
sent.

.. _nubus-user-management-self-service-registration-verification-email-figure:

.. figure:: /images/users_self-service_verification_email.*
   :alt: Sending the verification email

   Sending the verification email

Aspects about the *verification email* and the verification token can be
configured with the following Univention Configuration Registry variables. These Univention
Configuration Registry variables have to be set on
the :program:`Self Service Backend` that is defined via the Univention Configuration Registry
variable
:envvar:`self-service/backend-server`, since requests regarding these variables
are forwarded to the :program:`Self Service Backend`.

.. envvar:: umc/self-service/account-verification/email/webserver_address

   Defines the ``host`` part to use in the verification link URL. The default is
   to use the FQDN of the :program:`Self Service Backend` defined via the
   Univention Configuration Registry variable :envvar:`self-service/backend-server` since this
   Univention Configuration Registry variable is
   evaluated there.

.. envvar:: umc/self-service/account-verification/email/sender_address

   Defines the sender address of the verification email. Default is :samp:`Account
   Verification Service <noreply@{FQDN}>`.

.. envvar:: umc/self-service/account-verification/email/server

   Server name or IP address of the mail server to use.

.. envvar:: umc/self-service/account-verification/email/text_file

   A path to a text file whose content will be used for the body of the
   verification email. The text can contain the following strings which will be
   substituted accordingly: ``{link}``, ``{token}``, ``{tokenlink}`` and
   ``{username}``. As default the file
   :file:`/usr/share/univention-self-service/email_bodies/verification_email_body.txt`
   is used.

.. envvar:: umc/self-service/account-verification/email/token_length

   Defines the number of characters that is used for the verification token.
   Defaults to ``64``.

.. _end-user-self-service-registration-account-verification:

Account verification
--------------------

Following the verification link from the email, the user will land on
the *Account verification* page of the :program:`Self Service`.

.. _nubus-user-management-self-service-registration-account-verification-figure:

.. figure:: /images/users_self-service_verification.*
   :alt: Account verification

   Account verification

The account verification and request of new verification tokens can be
disabled/enabled with the Univention Configuration Registry variable
:envvar:`umc/self-service/account-verification/backend/enabled`. This Univention Configuration
Registry variable
has to be set on the systems that is defined as :program:`Self Service Backend`
via the Univention Configuration Registry variable :envvar:`self-service/backend-server`.

.. _nubus-user-management-self-service-registration-account-verification-message-figure:

.. figure:: /images/users_self-service_verification_message.*
   :alt: Account verification message

   Account verification message

The SSO login can be configured to deny login from unverified, self
registered accounts. This is configured through the Univention Configuration Registry variable
:envvar:`saml/idp/selfservice/check_email_verification`. This
needs to be set on the UCS Primary Directory Node and all UCS Backup Directory Nodes. The setting
has no effect on accounts created by an administrator.

The message on the SSO login page for unverified, self registered
accounts, can be set with the Univention Configuration Registry variables
:envvar:`saml/idp/selfservice/account-verification/error-title`
and
:envvar:`saml/idp/selfservice/account-verification/error-descr`. A localized
message can be configured by adding a *locale* like ``en`` to the variable, for
example :samp:`saml/idp/selfservice/account-verification/error-title/{en}`.

If the :program:`Keycloak` app is used as identity provider
see :external+uv-keycloak-app:ref:`app-settings` in the :cite:t:`ucs-keycloak-doc`
for the corresponding settings.

.. _end-user-self-service-deregistration:

Self deregistration
===================

The :program:`Self Service` allows for users to request the deletion of their
own account. This feature can be activated with the Univention Configuration Registry variable
:envvar:`umc/self-service/account-deregistration/enabled`, which will show a
:guilabel:`Delete my account` Button on the *Your profile* page of the Self
Service (:external+uv-nubus-manual:ref:`nubus-user-templates`).

If a user has requested to delete their account, it will not be deleted directly
but deactivated. In addition the ``DeregisteredThroughSelfService`` attribute of
the user will be set to ``TRUE`` and the ``DeregistrationTimestamp`` attribute
of the user will be set to the current time in the `GeneralizedTime LDAP syntax
<ldap-generalized-time_>`_. If the user has a ``PasswordRecoveryEmail`` set they
will receive a notification email which can be configured with the following
Univention Configuration Registry variables.

.. envvar:: umc/self-service/account-deregistration/email/sender_address

   Defines the sender address of the email. Default is :samp:`Password Reset Service
   <noreply@{FQDN}>`.

.. envvar:: umc/self-service/account-deregistration/email/server

   Server name or IP address of the mail server to use.

.. envvar:: umc/self-service/account-deregistration/email/text_file

   A path to a text file whose content will be used for the body of the email.
   The text can contain the following strings which will be substituted
   accordingly: ``{username}``. As default the file
   :file:`/usr/share/univention-self-service/email_bodies/deregistration_notification_email_body.txt`
   is used.

The Self Service provides a script under
:file:`/usr/share/univention-self-service/delete_deregistered_accounts.py` that
can be used to delete all users/user objects which have
``DeregisteredThroughSelfService`` set to ``TRUE`` and whose
``DeregistrationTimestamp`` is older than a specified time.

The following command would delete users whose ``DeregistrationTimestamp`` is
older than 5 days and 2 hours:

.. code-block::

   $ /usr/share/univention-self-service/delete_deregistered_accounts.py \
     --timedelta-days 5 \
     --timedelta-hours 2

For all possible arguments to the script see:

.. code-block::

   $ /usr/share/univention-self-service/delete_deregistered_accounts.py --help


The script can be run regularly by creating a cron job via Univention Configuration Registry variable.

.. code-block::

   $ ucr set cron/delete_deregistered_accounts/command=\
   /usr/share/univention-self-service/delete_deregistered_accounts.py\
   ' --timedelta-days 30'\
     cron/delete_deregistered_accounts/time='00 06 * * *'  # daily at 06:00


More information on how to set cron jobs via Univention Configuration Registry variable can be found in
:external+uv-ucs-manual:ref:`computers-defining-cron-jobs-in-univention-configuration-registry`.

.. _ldap-generalized-time: https://ldapwiki.com/wiki/Wiki.jsp?page=GeneralizedTime
