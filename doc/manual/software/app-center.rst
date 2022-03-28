
.. _software-appcenter:

Univention App Center
=====================

The Univention App Center allows simple integration of software components in a
UCS domain. The applications are provided both by third parties and by
Univention itself (e.g., UCS\@school). The maintenance and support for the
applications are provided by the respective manufacturer.

.. _appcenter-overview:

.. figure:: /images/appcenter_overview.*
   :alt: Overview of applications available in the App Center

   Overview of applications available in the App Center

The Univention App Center can be opened via the UMC module :guilabel:`App
Center`. It shows by default all installed as well as available software
components. :guilabel:`Search Apps...` can be used to search for available
applications. Furthermore, the applications can also be filtered using the
:guilabel:`Category` panel. More filters like the :emphasis:`Badges` and the
:emphasis:`App License` can be used. For example, the view can be limited to
applications with the categories ``Education`` or ``Office``. To only show the
``Recommended Apps`` for theses categories, it is sufficient to activate the
appropriate filter.

If you click on one of the displayed applications, further details on it are
shown (e.g., description, manufacturer, contact information and screenshots or
videos). The *Notification* field displays whether the manufacturer of the
software component is notified when it is installed/uninstalled. A rough
classification of the licensing can be found under the *License* section. Some
applications provide a :guilabel:`Buy` button with a link to detailed licensing
information. For all other applications, it is recommended to contact the
manufacturer of the application about detailed licensing information using the
e-mail address shown under *Contact*.

.. _appcenter-details:

.. figure:: /images/appcenter_details.*
   :alt: Details for an application in the App Center

   Details for an application in the App Center

With *Vote Apps* there is a special form of Apps in the App Center that do not
install anything on the UCS system. Voting helps Univention and the potential
app provider to determine the interest in this app. Vote apps are usually only
displayed for a limited voting period. That Vote Apps are available, can be
recognized by the shown *Vote Apps* filter option in the App Center overview.

.. _appcenter-vote-apps:

.. figure:: /images/vote_apps.*
   :alt: Example Vote Apps in App Center overview and detail view

   Example Vote Apps in App Center overview and detail view

Some applications may not be compatible with other software packages from UCS.
For instance, most groupware packages require the UCS mail stack to be
uninstalled. Every application checks whether incompatible versions are
installed and then prompts which *Conflicts* exist and how they can be
resolved. The installation of these packages is then prevented until the
conflicts have been resolved.

Some components integrate packages that need to be installed on the
|UCSPRIMARYDN| (usually LDAP schema extensions or new modules for the UCS
management system). These packages are automatically installed on the
|UCSPRIMARYDN|. If this is not possible, the installation is aborted. In
addition, the packages are set up on all accessible |UCSBACKUPDN| systems. If
several UCS systems are available in the domain, it can be selected on which
system the application is to be installed.

Some applications use the container technology :program:`Docker`. In these
cases, the application (and its direct environment) is encapsulated from the
rest and both security as well as the compatibility with other applications are
increased.

From a technical perspective, the app is started as Docker container and joined
into the UCS domain as |UCSMANAGEDNODE|. A corresponding computer object is
created for the |UCSMANAGEDNODE| in the LDAP directory.

On the network side, the container can only be reached from the computer on
which the app is installed. The app can, however, open certain ports, which can
be forwarded from the actual computer to the container. UCS' firewall is
correspondingly configured automatically to allow access to these ports.

If a command line is required in the app's environment, the first step is to
switch to the container. This can be done by running the following command
(using the fictitious app :program:`demo-docker-app` as an example in this
case):

.. code-block:: console

   $ univention-app shell demo-docker-app


Docker apps can be further configured via the UMC module. The app can be started
and stopped and the *autostart* option be set:

Started automatically
   ensures that the app is started automatically when the server is started up.

Started manually
   prevents the app from starting automatically, but it can be started via the
   UMC module.

Starting is prevented
   prevents the app from starting at any time; it cannot even be started via the
   UMC module.

In addition, apps can also be adjusted using additional parameters. The menu for
doing so can be opened using the :guilabel:`App Settings` button of an installed
app.

.. _appcenter-configure:

.. figure:: /images/appcenter_configure.*
   :alt: Setting of an application in the App Center

   Setting of an application in the App Center

After its installation, one or several new options are shown when
clicking on the icon of an application:

:guilabel:`Uninstall`
   removes an application.

:guilabel:`Open`
   refers you to a website or a UMC module with which you can further configure
   or use the installed application. This option is not displayed for
   applications which do not have a web interface or a UMC module.

Updates for applications are published independently of the |UCSUCS| release
cycles. If a new version of an application is available, the :guilabel:`Upgrade`
menu item is shown, which starts the installation of the new version. If updates
are available, a corresponding message is also shown in the UMC module
:guilabel:`Software update`.

Installations and the removal of packages are documented in the
:file:`/var/log/univention/management-console-module-appcenter.log` log file.
