.. _users-app-activation:

User activation for apps
========================

Many apps from the App Center are compatible with the central identity
management in UCS. This allows system administrators to activate the
users for apps. In some cases, app specific settings for the user can be
made. This depends on the app and how it uses the identity management.

.. _user-app-activation:

.. figure:: /images/user_activation.*
   :alt: User activation for installed apps

   User activation for installed apps

Once an app with user activation is installed in the UCS environment, it will
appear with the logo in the :guilabel:`Apps` tab of the user in the UMC module
*Users*. With a tick in the checkbox the user is activated for the app. If the
app offers specific settings another tab with the name of the app will appear to
set these parameters. The app activation and the parameters are stored at the
user object in the LDAP directory service.

To withdraw a user activation for an app, it is sufficient to deselect
the checkbox.

When the app is uninstalled, the checkbox of the user activation for the
app is removed from the :guilabel:`Apps` tab of the user in
the UMC module.
