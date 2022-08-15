.. _get-started:

***********
Get Started
***********

This chapter describes the requirements and the steps to create an app
for |UCSAPPC|. After reading this chapter an app provider will be able to
create their own app and start with a development and test cycle using
the Test App Center.

.. _app-provider-needs:

What does the app provider need?
================================

.. _app-provider-needs-docker-image:

Software in a Docker image
--------------------------

The software needs to be provided as a `Docker
image <docker-docs_>`_. This is the easiest way to deploy
software in |UCSAPPC|. It is also recommended to publish the Docker
container to `Docker hub <docker-hub_>`_. This makes
referencing the image later much easier and simplifies the development
and test cycle during development.

If public access to the image is not wanted, it can be made private. For
use on a UCS test machine during app development, the ``docker login``
needs to be used on the command-line to grant your machine access to the
private image. For the release of the app, the Univention team needs to
have access to the image. Please then grant access to the Docker Hub
user ``univention``. The image then has to be copied manually by the App
Center team to the Univention Docker registry, which cannot be browsed.
It needs credentials to be accessed. The Docker image should be
considered public by the time the app is published in |UCSAPPC|.

The image must have a version tag to distinguish different software
versions. It later allows updates for the apps.

.. _app-provider-needs-portal-account:

Account for App Provider Portal
-------------------------------

The App Provider Portal is the app developer's place for self service
for all the settings around the app.

1. To start building the app, an account for the App Provider Portal is
   needed. Please `request a personal
   account <univention-portal-account-request_>`_
   on the Univention website and provide some context about the intended
   app.

2. An email with username and instructions on how to set a password is
   sent.

3. Afterwards the login can be performed at the `App Provider
   Portal <univention-provider-portal_>`_.

4. After the login, the :guilabel:`Apps` module needs to be opened to work on the
   app.

.. _create-app-with-docker-portal-overview:

.. figure:: /images/app_portal_overview.png
   :alt: App Provider Portal overview with "Apps" module selected

   App Provider Portal overview with "Apps" module selected

.. _app-provider-needs-help:

Where to get help?
------------------

App providers that need technical help during their development process are
invited to open a topic in `Univention Forum
<univention-forum-apps_>`_. The dedicated section :guilabel:`App
Development` is for all questions around app development, debugging and the
like.

.. _create-app-with-docker:

Create an app with a Docker image
=================================

This section describes how to create the app in the App Provider Portal
and use a Docker image. It focuses on a single container setup. For a
setup with multiple containers with Docker Compose please see :ref:`Create a
Multi Container App <create-app-with-docker-compose>`.

.. _create-app-with-docker-create-app:

.. figure:: /images/app_portal_new_app.png
   :alt: Add new App
   :scale: 75%

   Add new App

1. In the App Provider Portal select :menuselection:`Favorites --> Apps` or
   :menuselection:`Software --> Apps`.

2. Click on :guilabel:`Add new app` and provide the following settings.

App ID
   is like a primary key. Choose it carefully, because it
   cannot be changed once the app is released to the public. It
   should only use small capitals, dashes and numbers. Please do not
   include version strings in here.

App name
   is the name of the app. It is used to display the app
   on the overview pages. This attribute can be changed any time.

App version
   is the version of the app. The App Center
   distinguishes versions and uses them to handle app updates. Once
   the app is released, this attribute cannot be changed.

UCS version
   is the UCS version the app should start to be
   available on. Simply start with the latest available UCS version.
   It can also be started with the oldest maintained UCS version to
   cover the broadest user base of UCS. See the `UCS maintenance
   cycle <ucs-maintenance-cycle_>`_
   for an overview of the maintained UCS version. In either case it
   is recommended to specify the supported UCS versions explicitly
   (see :ref:`Supported UCS
   versions <create-app-with-docker-supported-ucs-version>`.

Provider / Maintainer
   refers to the organization that the app
   belongs to. Please select your organization here or otherwise the
   app will not show up in the listing.

Docker app
   is for the recommended Docker based app. This
   documentation only covers single and multi container apps.

.. _create-app-with-docker-image:

Docker image
------------

1. In the app go to the tab :guilabel:`Configuration`.

2. Select the type of Docker app. This chapter discusses the :guilabel:`Single
   container app`, therefore please select it.

3. Enter the name of the image to :guilabel:`Docker image`. Grab the name of the
   image from Docker hub for example
   ``python:3.7-bullseye``.

.. important::

   Please add the version tag explicitly. The App Center distinguishes
   different app versions and handles updates accordingly.

.. _create-app-with-docker-supported-ucs-version:

Supported UCS versions
----------------------

Upon app creation the *UCS Version* has been specified. Please define
the supported UCS version explicitly on the :guilabel:`Version` tab in the
:guilabel:`Supported UCS versions` section.

Example: The app has been created for *UCS Version* ``4.4``. Two
entries for Supported UCS versions for App could be made: ``4.4-8`` and
``5.0-0``. This means that for the installation of the app UCS 4.4-8 or
UCS 5.0-0 are required.

.. _create-app-with-docker-description:

Logo and description
--------------------

On the app's :guilabel:`Presentation` tab please provide the display name and a
description in English and German and logos for the software. Start with
a short and a full description. It gives an impression on how it will
look like during later testing.

On the same tab two logos can be uploaded: A default icon that is shown
on the app tile in the overview. For optimal presentation it should be
more of a 1:1 ratio. The second can be more detailed and can for example
include the software name. Please provide the logos in SVG format.

Those settings can be changed later. For a more detailed description of
the app presentation and notes on the translation, please take a look at
:ref:`App presentation <app-presentation>`.

.. _create-app-with-docker-volumes:

Persistent data with volumes
----------------------------

By default files created inside a container are stored in it, but they
don't persist when the container is no longer running, removed or is
exchanged with a newer version. As solution Docker offers
`volumes <docker-docs-volumes_>`_, a mechanism for
persisting data generated and used by Docker containers. A volume is a
directory on the Docker host that is mounted inside the Docker
container.

To define volumes for the app, please activate them on the :guilabel:`Overview` tab
in the *Modules* section with the option :guilabel:`Docker app defines volumes`. Then
go to the :guilabel:`Volumes` tab. Add an entry for each volume and define the
directory or file path on the host in the first field and the
destination in the container in the second field. Leave the second field
empty for the same path.

For example:

Host
   ``/var/lib/app_etc``

Docker container
   ``/etc/app``

.. _create-app-with-docker-web-interface:

Web interface
-------------

Many Docker apps expose a web interface to the outside world, e.g. via
the port 8080. The App Center on UCS takes care to map this web
interface from some relative link to this port and adds a reverse proxy
configuration to the host's web server configuration.

On the :guilabel:`Web interface` tab, enter the relative path and which ports should
be proxied. For example, to map the container's ports 80 and 443 to
``/myapp``, the following settings have to be made:

Relative URL to web application
   ``/myapp``

HTTP port of web application
   ``80``

HTTPS port of web application
   ``443``

Supported protocols by the container's web interface
   Select :guilabel:`HTTP and HTTPS`, if both protocol schemes should be
   covered.

.. _create-app-with-docker-ports:

Ports
-----

If the app needs to occupy ports on the host that need to be passed
along to the container in order to work properly, they can be defined in
the *Ports* section on the :guilabel:`Web interface` tab. A list of ports can be
defined that the Docker host shall exclusively acquire for the Docker
container (:guilabel:`Port to be acquired exclusively`). Ports defined here cannot
be used by other services or other Docker containers on the UCS host. A
second list can be defined for ports that should be forwarded from the
host to the Docker container (:guilabel:`Host port to be forwarded`). Ports defined
here will build an implicit conflict list against other apps that want
to use these ports.

For example, the solution exposes the API under the dedicated port
``5555``. This port would be predestined to be defined here.

With the port definition the App Center also takes care to open them in
the UCS firewall. If additional firewall rules for ports are needed,
they can be defined in the app join script. Please refer to
:ref:`misc-nacl` in the UCS Developer Reference.

.. _create-app-with-docker-database:

Database
--------

Many applications need a relational database management system (RDMS)
somewhere in the environment to function properly. If the app needs such
a database the App Center takes care of providing one directly to the
Docker host. Activate :guilabel:`Docker app needs database` on the :guilabel:`Overview` tab in
the *Modules* section and then go to the :guilabel:`Database` tab, where the
appropriate settings can be made.

In the *Database* section the settings for the database are defined.
MariaDB and PostgreSQL are supported. Database user, database name and
the path to the password file can be specified. Upon installation of the
app, the App Center installs the defined database on the Docker host,
creates a database with the defined settings and saves the password in a
file for later use.

In the *Database environment variables* section, the mapping of the
database settings to the environment variables in the container are
defined. For example, if the container expects the database hostname in
``DATABASE_HOST``, it has to be entered into the field :guilabel:`Variable name for the
database host`. There are also fields for the database port, user,
password, database name and the password file.

.. _create-app-with-docker-environment:

Environment
-----------

Docker images usually receive environment variables when the container
is started. The App Center supports to pass static configuration options
to the container. Variables parameterized by |UCSUCRV|\ s are also
supported. An environment file can look like the following example:

.. code-block:: ini

   LDAP_SERVER=@%@ldap/server@%@
   FQDN=@%@hostname@%@.@%@domainname@%@
   HOME=/var/lib/univention-appcenter/apps/myapp/data/myapp_home

The content of the environment file can be entered in the App Provider
portal on the :guilabel:`Configuration` tab in the field for :guilabel:`Environment file for
Docker container creation`.

.. _create-app-with-docker-compose:

Create a Multi Container App
============================

|UCSAPPC| supports apps that consist of multiple Docker
images. It uses `Docker
Compose <docker-compose-docs_>`_, a tool for
defining and running multi-container Docker applications. The heart of
such applications is a YAML file that configures all services for the
application. The supported compose file format version is 2.0.

.. _create-app-with-docker-setup:

Multi container setup
---------------------

In order to create a Multi Container App, go to the :guilabel:`Configuration` tab in
the App Provider Portal, select :guilabel:`Multi container app with Docker compose`
and enter the content of your :file:`docker-compose.yml` file. A "flat" YAML
file must be used, because the implementation does currently not support
references to other files like for example files that should be mounted
inside a container or files listing environment variables.

|UCSUCR|, UCR for short, is the central tool for managing the local system
configuration of UCS (see
:ref:`uv-manual:computers-administration-of-local-system-configuration-with-univention-configuration-registry`).
Settings from UCR can be used in the Docker compose file to parameterize the
Docker setup. This comes in very handy when settings like for example the local
LDAP server should be passed to a container via its environment variables.

.. code-block:: yaml

   [...]
   services:
       [...]
       environment:
           ROOT_URL: https://@%@hostname@%@.@%@domainname@%@/$appid
           LDAP_Host: "@%@ldap/server/name@%@"
           LDAP_Port: "@%@ldap/server/port@%@"
           LDAP_BaseDN: "@%@ldap/base@%@"
           LDAP_Authentication_UserDN: "@%@appcenter/apps/$appid/hostdn@%@"
       [...]

The example above is an excerpt from a Docker compose file where
environment variables are defined for a service. The values of the
variables are set to the values of the given UCR variable. ``$appid``
needs to be replaced manually by you app id. UCR variables are enclosed
by ``@%@``. Please mind the double quotes in the example.

You also need to define the :guilabel:`Name of the "main" service within the
docker-compose.yml` below the :guilabel:`Contents of the docker-compose.yml file`.

In order to provide access to the application's web interface, please
see :ref:`Web interface <create-app-with-docker-web-interface>`.

If the app setup requires exclusive ports and a list of ports needs to
get forwarded from the host to the container, please see
:ref:`Ports <create-app-with-docker-ports>`.

.. _create-app-with-docker-script-reference:

Script execution reference
--------------------------

The App Center allows several scripts to be executed on the host and inside the
container during :ref:`installation <installation-scripts>`,
:ref:`uninstallation <uninstallation-scripts>` and :ref:`upgrade
<upgrade-scripts>`. Scripts run inside the container are run inside the
container of the "main service".

.. _create-app-with-docker-compose-postprocessing:

Post processing of Docker Compose file
--------------------------------------

Before a Multi Container App is started by the App Center, the
``docker-compose.yml`` is altered by the App Center with the following
changes:

1. When a Multi Container App is released, the ``docker-compose.yml`` is
   adjusted on the server side and the Docker Image information is
   changed to point to the Docker Images in the Univention Docker
   Registry. All Docker Images from published apps are copied to the
   Univention Docker Registry to be independent of
   `hub.docker.com <docker-hub_>`_. This is the only server-side
   change to the Docker Compose file.

2. The ``docker-compose.yml`` is itself a UCR template. As such, it will
   be interpreted by the App Center before being used. See
   :ref:`ucr-template` for details.

3. The App Center adds two standard volumes for the main service, as
   they are also included in Single Container Apps. These are the
   ``/var/lib/univention-appcenter/apps/$appid/data`` and
   ``/var/lib/univention-appcenter/apps/$appid/conf`` directories on the
   UCS host. If volumes are defined in the App Provider Portal in the
   App Configuration, these are also supplemented in
   ``docker-compose.yml`` by the App Center for the main service.

4. If ports are defined in the App Provider Portal, they are also added
   to ``docker-compose.yml``. Ports that have already been defined
   continue to exist. If the same port is defined in the portal and in
   ``docker-compose.yml``, the configuration in the App Provider Portal
   takes precedence. For example, if ``docker-compose.yml`` states that
   port ``4500`` is provided externally as port ``4500``, but the portal defines
   that this port is to be used as ``6500``, ``docker-compose.yml`` will be
   modified to map port ``4500`` to ``6500`` on the host.

5. If ``docker-compose.yml`` specifies that port ``80`` or ``443`` should be
   opened to the outside and the App Configuration specifies that these
   ports should be used by the App Center for the web interface, the App
   Center will define a port on the fly in ``docker-compose.yml``. This
   is because UCS hosts usually occupy ports 80 and 443 with a web
   server. The App Center creates an Apache Reverse Proxy configuration.
   See :ref:`Web interface <create-app-with-docker-web-interface>` for
   details.

6. UCS provides a number of environment variables via the App Center,
   e.g. parameters for an LDAP connection. The necessary variables are
   also written to ``docker-compose.yml`` in the *environments*
   section.

7. Furthermore, in the main service, as in Single Container Apps, all
   UCR variables defined on UCS are available under
   ``/etc/univention/base.conf``, as well as the password for the
   so-called machine account under ``/etc/machine.secret``.

As a result, Docker Compose starts a configuration on the UCS system
that no longer matches 100% of the App Provider's input. The modified
``docker-compose.yml`` can be found at
``/var/lib/univention-appcenter/apps/$appid/compose/docker-compose.yml``.

.. _ucr-template:

.. rubric:: UCR Template docker-compose file

As stated above, the ``docker-compose.yml`` is a UCR template. This means that
you are able to match the file to the environment of the Docker host. The UCS
Developer Reference contains more information about :ref:`UCR templates
<chap-ucr>`, but the core mechanics are:

1. Although every ``docker-compose.yml`` is a UCR template, you may not
   notice it: Where no specific tags are used, the very content is used.
   So if your file does not need any of the features mentioned below,
   just use your plain ``docker-compose.yml``.

2. You can add specific values of the configuration registry into your file.
   More importantly, this includes the App settings in :ref:`App
   settings <app-settings>` defined by the App itself:

   .. code-block:: yaml

      environment:
          MY_KEY: "@%@myapp/mysetting@%@"

   Note that App Settings are always added to the main service
   automatically. But this allows adding them to other containers and
   using them as part of a composite value.

3. You can do Python scripting within the template, e.g. to read (and
   write) the content of specific files.

   .. code-block:: yaml

      environment:
          MY_SECRET: "@!@import uuid; print(uuid.uuid4())@!@"

   Note that currently, you cannot access App Settings within the Python
   script.

.. _create-app-with-docker-finish:

Finish multi container setup
----------------------------

As soon as all the technical settings are made, please see :ref:`App life
cycle <app-lifecycle>` for the next steps and how to test the app.
For app presentation in the App Center please see :ref:`App
presentation <app-presentation>`.
