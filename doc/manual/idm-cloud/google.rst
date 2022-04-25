.. _idmcloud-gsuite:

Google Apps for Work Connector
==============================

Google Apps for Work Connector allows users and groups to synchronize to a G
Suite domain. You can control which of the users created in UCS are allowed to
use G Suite. The users selected in this way are provisioned accordingly by UCS
into the G Suite domain. It can be configured which attributes are synchronized
and attributes can be anonymized.

The single sign-on login to G Suite is done via the UCS integrated SAML
implementation. Authentication takes place against the UCS server, and no
password hashes are transferred to the G Suite domain. The user's authentication
is done exclusively via the client's web browser. However, the browser should
be able to resolve the DNS records of the UCS domain, which is particularly
important for mobile devices.

.. _idmcloud-gsuite-setup:

Setup
-----

To setup the Google Apps for Work Connectors a G Suite Administrator account, a
corresponding account in the G Suite domain, and a `domain verified
<google-domain-verify_>`_ by Google are required. The first two will be provided
free of charge by Google for testing purposes. However, configuring the SSO
requires a separate internet domain where TXT records can be created.

If no G Suite subscription is available yet, it can be configured via `Set up
Google Workspace for your organization <google-setup-workspace_>`_.
A connection with a private Gmail account is not possible.

Afterwards, you should sign in with a *G Suite administrator account* in the
`Admin Console <google-admin-console_>`_. The domain should now be verified.
For this it is necessary to create a TXT record in the DNS of your own domain.
This process can take a few minutes.

Now the Google Apps for Work Connector from the App Center can be installed on
the UCS system. The installation only takes a few minutes. There is a setup
wizard available for the initial configuration. After completing the wizard the
connector is ready for use.

.. _idmcloud-gsuite-wizard:

.. figure:: /images/google_wizard1.*
   :alt: Google Apps for Work Setup Wizard

   Google Apps for Work Setup Wizard

.. _idmcloud-gsuite-config:

Configuration
-------------

After the setup via the setup wizard, you can use the user module on each user
object on the *Google Apps tab* to configure that this user is provisioned to G
Suite.

If a change is made to the user, the changes will also be replicated to the G
Suite domain. There is no synchronization from the G Suite domain to the UCS
system. This means that changes made in the G Suite domain may be overwritten by
changes to the same attributes in UCS.

If the Google Apps property is removed from a user, the user will be deleted
from the G Suite domain accordingly.

The |UCSUCRV| :envvar:`google-apps/attributes/mapping/.*` is used to configure
which LDAP attributes (e.g. first name, last name, etc.) of a user account are
synchronized. The |UCSUCRV| and its values reflect the nested data structure of
the G Suite user accounts. The names that follow the percentage sign in the
values are the attributes in the UCS LDAP. If all |UCSUCRV|
:envvar:`google-apps/attributes/mapping/.*` are removed, no data other than the
primary email address is synchronized.

The |UCSUCRV| :envvar:`google-apps/attributes/anonymize` can be used to specify
comma-separated LDAP attributes that are created in the G Suite domain but
filled with random values.

The |UCSUCRV| :envvar:`google-apps/attributes/never` can be used to specify
comma-separated LDAP attributes that should not be synchronized, even if they
are configured via :envvar:`google-apps/attributes/mapping/.*` or
:envvar:`google-apps/attributes/anonymize`.

The synchronization of Google Apps for Work user groups can be enabled with the
|UCSUCRV| :envvar:`google-apps/groups/sync`.

Changes to |UCSUCRV| are implemented after restarting the |UCSUDL|.

.. _idmcloud-gsuite-debug:

Troubleshooting/Debugging
-------------------------

Messages during setup are logged in the following log file
:file:`/var/log/univention/management-console-module-googleapps.log`.

In case of synchronization problems, the log file of the |UCSUDL| should be
checked: :file:`/var/log/univention/listener.log`. The |UCSUCRV|
:envvar:`google-apps/debug/werror` activates additional debug output.
