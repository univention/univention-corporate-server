.. _user-management-password-changes-by-users:

User self services
==================

.. _user-management-password-changes-by-users-via-umc:

Password change by user via UCS portal page
-------------------------------------------

Every logged in user can change their own password by opening the menu via the
hamburger icon in the top right corner and selecting :menuselection:`User settings -->
Change password`. The change is performed directly via the PAM stack (see
:ref:`computers-Authentication-PAM`) and is then available centrally for all
services.

.. _user-management-password-changes-by-users-self-service:

Password management via Self Service app
----------------------------------------

By installing the UCS components :program:`Self Service Backend` and
:program:`Self Service` in the domain via the :guilabel:`App Center`, users are
enabled to take care of their password management without administrator
interaction.

The :program:`Self Service` app creates its own portal, accessible at the web
URI ``/univention/selfservice/``, which bundles all its functionality. The
original portal has the same entries registered at its user menu. They allow
users to update their password given their old password as well as to reset
their lost password by requesting a token to be sent to a previously registered
contact email address. The token has to be entered on the dedicated password
reset web page.

The following |UCSUCRV|\ s can be used to activate or deactivate individual
features of the password management.

.. envvar:: umc/self-service/passwordreset/backend/enabled

   Activates or deactivates the backend of the *Password forgotten* page. This
   |UCSUCRV| has to be set on the systems that is defined as :program:`Self
   Service backend` via the |UCSUCRV| :envvar:`self-service/backend-server`,
   since requests regarding these variables are forwarded to the :program:`Self
   Service backend`.

.. envvar:: umc/self-service/protect-account/backend/enabled

   Activates or deactivates the backend of the *Protect account* page. This
   |UCSUCRV| has to be set on the systems that is defined as :program:`Self
   Service backend` via the |UCSUCRV| :envvar:`self-service/backend-server`,
   since requests regarding these variables are forwarded to the :program:`Self
   Service backend`.

.. envvar:: umc/self-service/service-specific-passwords/backend/enabled

   Activates or deactivates the backend for service specific passwords.
   Currently, only the service RADIUS is supported. Find more information in
   :ref:`ip-config-radius-configuration-service-specific-password`.

Those variables also activate or deactivate the corresponding entries in the
portal. However, you can also adjust them manually, they are in fact just normal
portal entries.

.. _user-management-password-changes-by-users-contact-data:

Contact information
-------------------

Additional personal data can be stored in LDAP with the users account.
This may include a picture, the users private address and other contact
information. By default only administrators can modify them. As an
alternative selected attributes may be unlocked for the user to change
himself. The user then can do this using the :program:`Self Service` app.

.. _user-self-service:

.. figure:: /images/users_self-service_profile.*
   :alt: User profile self-service

   User profile self-service

For this the following |UCSUCRV|\ s must be configured:



.. envvar:: self-service/ldap_attributes

   This variable configures the *LDAP* attributes a user can modify at its own
   user account. The names of the attributes must be separated by comma. This
   variable must be set on |UCSPRIMARYDN| (and |UCSBACKUPDN|\ s).

.. envvar:: self-service/udm_attributes

   This variable configures the *UDM* attributes a user can modify. The names of
   the attributes must be separated by comma. This variable must be set on all
   hosts, where the :program:`Self Service` app is installed (incl. |UCSPRIMARYDN|).

.. envvar:: umc/self-service/profiledata/enabled

   This variable must be set to ``true`` on all involved server systems to
   enable the mechanism.

.. envvar:: umc/self-service/allow-authenticated-use

   This variable defines whether the specification of user name and password is
   necessary when opening and modifying your own user profile if you are already
   logged in to Univention Portal.

   As of UCS 4.4-7, this |UCSUCRV| is automatically set to ``true`` when the
   :program:`Self Service` is installed for the first time. The ``true`` value
   activates the use of an existing Univention Portal session. The fields
   *Username* and *Password* are then automatically filled in or no longer
   displayed.

   Systems upgraded to UCS 4.4-7 will retain the old behavior by automatically
   setting the value to ``false``. Note that this variable must be set to the
   same value on all participating systems where the :program:`Self Service` app
   is installed (incl. |UCSPRIMARYDN|).


Both ``*attributes`` variables must match each other. The names of the
attributes and their mapping can be fetched from the following command:

.. code-block::

   $ python3 -c 'from univention.admin.handlers.users.user import mapping;\
   > print("\n".join( \
   > map("{0[0]:>30s} {0[1][0]:<30s}".format, sorted(mapping._map.items()))) \
   > )'

.. _user-management-password-changes-by-users-selfregistration:

Self registration
-----------------

The Self Service allows for users to register themselves, which will create a
user account that has to be verified via email.

User accounts that are created via the Self Service will have the
``RegisteredThroughSelfService`` attribute of the user set to ``TRUE`` and the
``PasswordRecoveryEmailVerified`` attribute set to FALSE. After the user has
verified their account via the verification email the
``PasswordRecoveryEmailVerified`` attribute will be set to ``TRUE``.

.. _user-management-password-changes-by-users-selfregistration-account-creation:

Account creation
~~~~~~~~~~~~~~~~

.. _user-registration:

.. figure:: /images/users_self-service_registration.*
   :alt: Account registration

   Account registration

Aspects about the *Create an account* page and the account creation
itself can be configured with the following |UCSUCRV|\ s. These |UCSUCRV|\ s
have to be set on the systems that is defined as :program:`Self Service Backend`
via the |UCSUCRV| :envvar:`self-service/backend-server`, since
requests regarding these variables are forwarded to the Self Service
backend.

.. envvar:: umc/self-service/account-registration/backend/enabled

   With this variable the account registration can be disabled/enabled.

.. envvar:: umc/self-service/account-registration/usertemplate

   With this variable a user template (:ref:`users-templates`) can be specified
   that will be used for the creation of self registered accounts.

.. envvar:: umc/self-service/account-registration/usercontainer

   With this variable a container can be specified under which the self
   registered users are created.

.. envvar:: umc/self-service/account-registration/udm_attributes

   This variable configures which UDM attributes of a user account are shown on
   the *Create an account* page of the Self Service. The names of the UDM
   attributes must be provided as a comma separated list.

.. envvar:: umc/self-service/account-registration/udm_attributes/required

   This variable configures which of the UDM attributes set via the |UCSUCRV|
   :envvar:`umc/self-service/account-registration/udm_attributes` are required
   for the user to provide. The names of the UDM attributes must be provided as
   a comma separated list.

.. _user-management-password-changes-by-users-selfregistration-verification-email:

Verification email
~~~~~~~~~~~~~~~~~~

After a user has clicked on :guilabel:`Create account`, they
will see a message that an email for the account verification has been
sent.

.. _user-verification-email:

.. figure:: /images/users_self-service_verification_email.*
   :alt: Sending the verification email

   Sending the verification email

Aspects about the verification email and the verification token can be
configured with the following |UCSUCRV|\ s. These |UCSUCRV|\ s have to be set on
the :program:`Self Service Backend` that is defined via the |UCSUCRV|
:envvar:`self-service/backend-server`, since requests regarding these variables
are forwarded to the :program:`Self Service Backend`.

.. envvar:: umc/self-service/account-verification/email/webserver_address

   Defines the ``host`` part to use in the verification link URL. The default is
   to use the FQDN of the :program:`Self Service Backend` defined via the
   |UCSUCRV| :envvar:`self-service/backend-server` since this |UCSUCRV| is
   evaluated there.

.. envvar:: umc/self-service/account-verification/email/sender_address`

   Defines the sender address of the verification email. Default is ``Account
   Verification Service <noreply@FQDN>``.

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

.. _user-management-password-changes-by-users-selfregistration-account-verification:

Account verification
~~~~~~~~~~~~~~~~~~~~

Following the verification link from the email, the user will land on
the *Account verification* page of the :program:`Self Service`.

.. _user-verification:

.. figure:: /images/users_self-service_verification.*
   :alt: Account verification

   Account verification

The account verification and request of new verification tokens can be
disabled/enabled with the |UCSUCRV|
:envvar:`umc/self-service/account-verification/backend/enabled`. This |UCSUCRV|
has to be set on the systems that is defined as :program:`Self Service Backend`
via the |UCSUCRV| :envvar:`self-service/backend-server`.

.. _user-verification-message:


.. figure:: /images/users_self-service_verification_message.*
   :alt: Account verification message

   Account verification message

The SSO login can be configured to deny login from unverified, self
registered accounts. This is configured through the |UCSUCRV|
:envvar:`saml/idp/selfservice/check_email_verification`. This
needs to be set on the |UCSPRIMARYDN| and all |UCSBACKUPDN|\ s. The setting
has no effect on accounts created by an administrator.

The message on the SSO login page for unverified, self registered
accounts, can be set with the |UCSUCRV|\ s
:envvar:`saml/idp/selfservice/account-verification/error-title`
and
:envvar:`saml/idp/selfservice/account-verification/error-descr`.
A localized message can be configured by adding a local to the variable, for
example ``saml/idp/selfservice/account-verification/error-title/en``.

.. _user-management-password-changes-by-users-selfderegistration:

Self deregistration
-------------------

The :program:`Self Service` allows for users to request the deletion of their
own account. This feature can be activated with the |UCSUCRV|
:envvar:`umc/self-service/account-deregistration/enabled`, which will show a
:guilabel:`Delete my account` Button on the *Your profile* page of the Self
Service (:ref:`users-templates`).

If a user has requested to delete their account, it will not be deleted directly
but deactivated. In addition the ``DeregisteredThroughSelfService`` attribute of
the user will be set to ``TRUE`` and the ``DeregistrationTimestamp`` attribute
of the user will be set to the current time in the `GeneralizedTime LDAP syntax
<ldap-generalized-time_>`_. If the user has a ``PasswordRecoveryEmail`` set they
will receive a notification email which can be configured with the following
|UCSUCRV|\ s.

.. envvar:: umc/self-service/account-deregistration/email/sender_address

   Defines the sender address of the email. Default is ``Password Reset Service
   <noreply@FQDN>``.

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
   > --timedelta-days 5 \
   > --timedelta-hours 2

For all possible arguments to the script see:

.. code-block::

   $ /usr/share/univention-self-service/delete_deregistered_accounts.py --help


The script can be run regularly by creating a cron job via |UCSUCR|.

.. code-block::

   $ ucr set cron/delete_deregistered_accounts/command=\
   > /usr/share/univention-self-service/delete_deregistered_accounts.py\
   > ' --timedelta-days 30' \
   > cron/delete_deregistered_accounts/time='00 06 * * *'  # daily at 06:00


More information on how to set cron jobs via |UCSUCR| can be found in
:ref:`computers-Defining-cron-jobs-in-Univention-Configuration-Registry`.
