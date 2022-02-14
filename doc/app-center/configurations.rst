.. _configurations:

App configurations
==================

The App Center offers the possibility to add scripts at various points
during the installation and configuration of the app. The scripts are
described below. They can be edited in the app in the App Provider
portal in the following sections:

-  Scripts AR Join & unjoin script

-  Scripts AR Scripts called before App Center action on apps

-  Scripts AR Scripts for data store and restore ``store_data``,
   ``restore_data_before_setup``, ``restore_data_after_setup``

-  Scripts AR Setup script

-  Scripts AR Configure scripts. (``configure``)

-  Scripts AR Configure scripts. (``configure_host``)

.. _installation-scripts:

Installation scripts
--------------------

During the installation of an app, various scripts are called. Please
see the overview below about of the involved scripts and the parameters
they are called with. More information on the scripts themselves can be
found in the following sections.

.. figure:: /images/app-flow-install.png
   :alt: App workflow for installation

   App workflow for installation

.. _installation:preinst:

Script called before installation to verify that App may be installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``preinst`` script is executed on the UCS host system before the app
is initialized, even before the app image is downloaded. Its purpose is
to check whether installation will be successful or not. Any exit code
other than 0 will result in cancellation of the installation process.
This script is also executed if the app is upgraded.

The script receives the LDAP bind DN of the Administrator account and
its password, the version of the app that should be installed, the
locale and an error log file for log output as parameters. Error
messages in the passed error log file will be passed to the UCS
management system and thus to the administrator performing the
installation. Proper error messages can thus be passed to the
administrator.

Note that :ref:`App settings <app-settings>` with scope ``outside`` are
already set by the time the script is run and can therefore be checked
against.

.. _installation:restore-data-before-setup:

Docker script restore_data_before_setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``restore_data_before_setup`` is executed inside
the Docker container before the ``setup`` script is run. Its purpose is
to restore the data which has been stored by the ``store_data`` script.
The parameters are the *appid*, the app version and a filename for error
logging.

.. _installation:setup:

Docker script setup
~~~~~~~~~~~~~~~~~~~

The life cycle script ``setup`` is executed inside the Docker container.
It is the heart of the initial app configuration and typically used to
make environment specific settings to the container or apply certain
changes that require the container environment. If the script fails
(exit code != 0) the installation is aborted.

The parameters given to the script are the *appid*, the app version, a
filename for error logging and the username and credentials for the
Administrator user.

.. _installation:restore_data_after_setup:

Docker script restore_data_after_setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``restore_data_after_setup`` is executed inside
the Docker container after the ``setup`` script is run. Its purpose is
to restore the data which has been stored by the ``store_data`` script.
The parameters are the *appid*, the app version and a filename for error
logging.

.. _installation:configure_host:

Settings script run on Docker host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure_host`` is executed on the Docker host
after the ``restore_data_after_setup`` script is run. Its purpose is to
make environment specific settings on the UCS host regarding the app.
The parameters are the app action ``install``, the app version, a
filename for error logging and the locale.

.. _installation:configure:

Settings script run in Docker container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure`` is executed inside the Docker
container after the ``configure_host`` script. Its purpose is to make
environment specific settings in the app container. The parameters are
the app action ``install``, the *appid*, the app version and a filename
for error logging.

.. _installation:joinscript:

Join script
~~~~~~~~~~~

The joinscript ``inst`` is executed on the UCS host system after the
Docker container is configured. Please refer to the `Developer
Reference <https://docs.software-univention.de/developer-reference-5.0.html#chap:join>`__
about how to write a join script. In principle a join script is a script
that runs after the installation of an app and it has write access to
the LDAP directory service. If it runs successfully, the join script may
save this information in a status file. If this does not happen, the
user is constantly reminded to re-run the join script. So the join
script does not need to run successfully. The installation will not be
aborted at this point. But of course at some point it should run through
successfully.

.. _installation:joinscript:helper:

Join script helper
^^^^^^^^^^^^^^^^^^

Apart from the functions documented in the Developer Reference, the
below listed functions are available in join scripts for dealing with
apps. They require the following line in the script:

.. code:: sh

   . /usr/share/univention-appcenter/joinscripthelper.sh
                       

Furthermore, this call provides access to the following variables:

$APP
   app id

$APP_VERSION
   app version

$SERVICE
   app name

$CONTAINER
   Docker container id

.. _installation:joinscript:functions:

Join script functions
^^^^^^^^^^^^^^^^^^^^^

``joinscript_add_simple_app_system_user`` adds a domain wide user to the
LDAP directory that is not a real Domain User and offers an
authentication account. It can be used as bind user for the app to
connect to the LDAP directory. The password will be stored on the Docker
Host at ``/etc/$APP.secret``. The DN will be
``uid=$APP-systemuser,cn=users,$ldap_base``.

.. code:: sh

   joinscript_add_simple_app_system_user "$@" --set mailPrimaryAddress=...
                       

``joinscript_container_is_running`` returns whether or not the Docker
container is currently running. 0: Yes, 1: No. Can be used in an if
statement.

.. code:: sh

   joinscript_container_is_running || die "Container is not running"
                       

``joinscript_run_in_container`` runs one command inside the container.
Returns the return code of the command.

.. code:: sh

   joinscript_run_in_container service myapp restart ||
   die "Could not restart the service"
                       

``joinscript_container_file`` prints the absolute path for the Docker
host for the filename given inside the container.

.. code:: sh

   FILENAME="$(joinscript_container_file "/opt/$APP/my.cnf")"
                       

``joinscript_container_file_touch`` creates a file inside the container.
Directories are created along the way. Prints the resulting filename
just like "joinscript_container_file".

``joinscript_register_schema`` registers a LDAP schema file semi
automatically. The schema file allows to extend LDAP objects with new
attributes. The file will be copied to the Docker host's
``/usr/share/univention-appcenter/apps/APPID/APPID.schema`` during
installation. See the `LDAP
documentation <http://www.openldap.org/doc/admin24/schema.html>`__ for
the syntax of a schema file. If an official object identifier (OID)
namespace is needed, Univention can provide one. It is important to note
that shipping the schema file alone is not enough. It has to be
registered with the mentioned function in the join script. The schema
file content can be provided in the App Provider portal on the Identity
management tab in the User rights management section, in the field for
Schema extension for LDAP.

.. code:: sh

   joinscript_register_schema "$@"
                       

.. _installation:joinscript:boilerplate:

Join script boilerplate
^^^^^^^^^^^^^^^^^^^^^^^

The following boilerplate can be used as a starting point for the app's
own join script.

.. code:: sh

   #!/bin/bash
   VERSION=1

   . /usr/share/univention-appcenter/joinscripthelper.sh
   joinscript_init
   eval "$(univention-config-registry shell)"
   ucs_addServiceToLocalhost "$SERVICE" "$@"

   ... # Place for the app's join script code

   joinscript_save_current_version
   exit 0
                       
.. _uninstallation-scripts:

Uninstallation scripts
----------------------

During the uninstallation of an app, various scripts are called. Please
see the overview below about the involved scripts and the parameters
they are called with. More information on the scripts themselves can be
found in the following sections.

.. figure:: /images/app-flow-remove.png
   :alt: App workflow for Removal

   App workflow for Removal

.. _uninstallation:prerm:

Script called before uninstalling to verify that App may be removed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``prerm`` script is executed on the UCS host system. Its purpose is
to check the prerequisites for an uninstallation and abort if they are
not met. For example, the prerm may fail if other software still depends
on it. Any exit code other than 0 will result in cancellation of the
uninstallation process. The given parameters are the LDAP bind DN of the
Administrator account and its password, the version of the app that
should be uninstalled/removed, the locale and an error log file for log
output. Error messages in the passed error log file will be passed to
the UCS management system and thus to the administrator performing the
installation. Proper error messages can thus be passed to the
administrator.

.. _uninstallation:configure_host:

Settings script run on Docker host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure_host`` is executed on the Docker host
after the ``prerm`` script is run. Its purpose is to make environment
specific settings on the UCS host during the removal of the app. The
parameters are the app action ``remove``, the app version, a filename
for error logging and the locale.

.. _uninstallation:configure:

Settings script run in Docker container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure`` is executed inside the Docker
container after the ``configure_host`` script. Its purpose is to make
environment specific settings in the app container before it is removed.
The parameters are the app action ``remove``, the *appid*, the app
version and a filename for error logging.

.. _uninstallation:store-data:

Docker script store_data
~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``store_data`` is required if data exists in the
container which should not be removed when the container is replaced
with a new container or if the app is uninstalled. The script is not
required if all the data is stored outside of the container for example
in a database or a mapped volume. It is executed inside the Docker
container and it should copy the relevant data to
``/var/lib/univention-appcenter/apps/$APPID/data/``. Afterwards, the
data can be restored by one of the ``restore_data*`` scripts. The
parameters are the *appid*, the app version and a filename for error
logging.

.. _uninstallation:unjoin:

Unjoin script
~~~~~~~~~~~~~

The unjoin script ``uinst`` is executed on the UCS host system after the
Docker container is removed. See the for how to write an unjoin script.
It should revert most (if not all) changes done in the join script. With
the notable exception of schema registration. An LDAP schema extension
should never be removed once it was registered.

.. _upgrade-scripts:

Upgrade scripts
---------------

It may be necessary to move data from the old container to the new
container when the app container is replaced during an upgrade or when
the app is uninstalled. The upgrade scripts can be used for this
purpose. Please see an overview of the involved scripts and the
parameters they are called with in the figure below. More information on
the scripts themselves can be found in the following sections.

.. figure:: /images/app-flow-update.png
   :alt: App workflow for upgrade

   App workflow for upgrade


.. _upgrade-scripts:preinst:

Script called before upgrade to verify that App may be upgraded
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``preinst`` script is executed on the UCS host system before the app
upgrade is initialized, even before the Docker image is downloaded. Its
purpose is to check whether the requirements for the upgrade are
fulfilled. Any exit code other than 0 will result in cancellation of the
upgrade process.

The script receives the LDAP bind DN of the Administrator account and
its password, the old version of the app and the new version, the locale
and an error log file for log output as parameters. Error messages in
the passed error log file will be passed to the UCS management system
and thus to the administrator performing the installation. Proper error
messages can thus be passed to the administrator.

.. _upgrade:store_data:

Docker script store_data
~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``store_data`` is required if data exists in the
container which should not be removed when it is replaced with a new
container or if the app is uninstalled. It is not required if all the
data is stored outside the container for example in a database or a
mapped volume. The script is executed inside the Docker container and it
should copy the relevant data to
``/var/lib/univention-appcenter/apps/$APPID/data/``. Afterwards, the
data can be restored by one of the ``restore_data*`` scripts when they
are executed in the new container.

.. _upgrade:restore_data_before_setup:

Docker script restore_data_before_setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``restore_data_before_setup`` is executed inside
the Docker container before the ``setup`` script is run. Its purpose is
to restore the data which has been stored by the ``store_data`` script.

.. _upgrade:setup:

Docker script setup
~~~~~~~~~~~~~~~~~~~

The life cycle script ``setup`` is executed inside the Docker container.
It is used to make environment specific settings to the new container or
apply certain changes that require the container environment. If the
script fails (exit code != 0) the upgrade is aborted.

The parameters given to the script are the *appid*, the app version, a
filename for error logging and the username and credentials for the
Administrator user.

.. _upgrade:restore_data_after_setup:

Docker script restore_data_after_setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The life cycle script ``restore_data_after_setup`` is executed inside
the Docker container after the ``setup`` script is run. Its purpose is
to restore the data which has been stored by the ``store_data`` script
in the old container.

.. _upgrade:configure_host:

Settings script run on Docker host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure_host`` is executed on the Docker host
after the ``restore_data_after_setup`` script is run. Its purpose is to
make environment specific settings on the UCS host regarding the app
during the upgrade. The parameters are the app action ``upgrade``, the
app version, a filename for error logging and the locale.

.. _upgrade:configure:

Settings script run in Docker container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The settings script ``configure`` is executed inside the Docker
container after the ``configure_host`` script is run. Its purpose is to
make environment specific settings in the app container during the
upgrade. The parameters are the app action ``upgrade``, the *appid*, the
app version and a filename for error logging.

.. _upgrade:joinscript:

Join Script
~~~~~~~~~~~

Finally, the join script ``inst`` is called to end the upgrade. With an
updated join script changes can be made to the environment that require
the necessary execution permissions or access to the UCS directory
service. When a join script should run during the upgrade, please keep
in mind to increment the ``VERSION`` counter. For more information on
the join script in general see :ref:`Join
script <installation:joinscript>`.

.. _app-settings:

App settings
------------

The App settings allow the user to configure the app during its runtime.
The App Provider Portal can be used to define which settings are
displayed to the user. The app can react accordingly to the changes.

If App settings are defined for an app, the user can reach these
settings in the app configuration, see
:ref:`app-configurations:app-settings:button`).

.. _app-configurations:app-settings:button:

.. figure:: /images/Appcenter-settings-button.png
   :alt: App settings button

   App settings button

An example for an App settings dialog is in
:ref:`app-configurations:app-settings:example`).

.. _app-configurations:app-settings:example:

.. figure:: /images/Appcenter-settings-example.png
   :alt: App settings example

   App settings example

The App settings can be defined on the tab Advanced in the section App
settings in the App Provider Portal.

.. _app-settings:scripts:

React on App settings
~~~~~~~~~~~~~~~~~~~~~

The settings are saved inside the Docker container in the file
``/etc/univention/base.conf`` in the format *key: value*. After the
settings are changed, two scripts are executed. First, the script
``configure_host``. This script is run on the Docker host. Second, the
script ``configure`` is executed. It is executed inside the Docker
container. In the App Provider Portal, the path of the script can be
given (Configure scripts) or the script code can be uploaded (Path to
script inside the container (absolute)).

.. _app-settings:reference:

App settings configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The App settings are defined in the ini format. The definition can be
done in the field Settings that can be used to configure the app. ini
file format. One ini file can contain several settings.

The name of a setting is the name of the section in the ini file, for
example

.. code:: ini

   [myapp/mysetting]
                       

It is recommended to use the app ID as a prefix to prevent collisions.

The type of the attribute is defined with the keyword *Type*. The
following types are supported:

String
   A standard input field with no restrictions. This is used by default.

Int
   A number field which is validated accordingly.

Bool
   A checkbox. The value ``true`` or ``false`` is set.

List
   A widget that lets the user choose from a predefined set of values.

Password
   A password input.

.. note::

   The content will be stored as clear text value inside the Docker container.

File
   An upload widget. The content is stored directly in a file according
   to the definition of the setting.

PasswordFile
   As a File, but shown as a password input.

Status
   A read-only settings that is actually meant as a feedback channel for
   the user. This does not render a widget, but instead just writes a
   text with whatever was written into this variable. Writing to it is
   up to the App Provider (e.g., by using the configure script).

The attribute Description is used to define the description of the
setting. It is shown next to the widget so that the user knows what to
do with this form. It can be localized by also defining Description[de]
and so on.

The attribute Group can be used to group settings. All settings sharing
one group will be put under that label. The default group is
``Settings``. It is also possible to localize it for example Group[de].

The attribute Show can be used to define when the setting should be
shown. By default the setting attribute is shown when the app is up and
running. It is also possible to show the setting attribute during the
installation. The following values are possible ``Install``,
``Upgrade``, ``Remove`` and ``Settings``. It is possible to specify more
than one value which must be separated by comma.

The attribute ShowReadOnly can be used in the same way as Show. The
difference is that the value is not changeable.

The attribute InitialValue can be used during the installation. If no
value for this attribute was given during the installation, the defined
value is set.

The attribute Required can be used to define if this setting has to be
set or not.

The attribute Scope is used to specify if the value is set inside the
Docker container (``inside``), on the Docker host (``outside``) or on
both (``inside, outside``). The default is ``inside``. Values in the
scope ``inside`` can be referenced in the ``docker-compose.yml`` for
multi container apps just like |UCSUCRVs| (see :ref:`Post processing of Docker
Compose file <create-app-with-docker:compose-postprocessing>` for an
example).

The attributes Labels and Values are used if a type List is defined. The
attribute Labels defines the values shown to the user and the attribute
Values defines the values which are stored. The lists are comma
separated and should have the same size. If a comma is necessary inside
a label or value, it can be escaped with a \\.

The attribute Filename can be used to define the absolute path where the
file should be stored. This attribute is needed in case the types File
or PasswordFile are used.

.. _app-settings:examples:

App settings examples
~~~~~~~~~~~~~~~~~~~~~

This is a minimal settings definition:

.. code:: ini

   [myapp/mysetting]
   Type = String
   Description = This is the description of the setting
   Description[de] = Das ist die Beschreibung der Einstellung
                   

These are two more advanced settings

.. code:: ini

   [myapp/myfile]
   Type = File
   Filename = /opt/myapp/license
   Description = License for the App
   Description[de] = Lizenz der App
   Show = Install, Settings
   Group = License and List
   Group[de] = Lizenz und Liste
                   

.. code:: ini

   [myapp/list]
   Type = List
   Description = List of values
   Show = Install
   ShowReadOnly = Settings
   Values = value1, value2, value3
   Labels = Label 1, Label 2, Label 3
   InitialValue = value2
   Scope = inside, outside
   Group = License and List
   Group[de] = Lizenz und Liste
                   

The first of these two settings will upload a file to
``/opt/myapp/license`` inside the container. The second will save
*myapp/list: value2* (or another value) inside the container and on the
Docker host. Both settings will be shown before the installation. On the
App settings page, the list setting will be read-only.

Certificates
------------

UCS provides a certificate infrastructure for secure communication
protocols. See `SSL certificate
management <https://docs.software-univention.de/manual-5.0.html#domain:ssl>`__
in the UCS manual.

Apps may need access to the UCS certificate infrastructure or need to be
aware of changes to the certificates. Starting with 91 the |UCSAPPC|
provides a simple way to manage certificates inside an app. The script
update-certificates is executed on the UCS host automatically during the
installation and upgrade of apps (but can also be executed manually) and
provides apps a simple way to gain access to certificates and to react
to changes to certificates.

.. code:: sh

   # update all apps
   univention-app update-certificates

   # update app "my-app"
   univention-app update-certificates my-app
               

What happens with ``update-certificates``?

-  The UCS root CA certificate is copied to
   ``/usr/local/share/ca-certificates/ucs.crt`` inside the container.

-  update-ca-certificates is executed in the Docker container, if it
   exists, to update the CA certificate list.

-  The UCS root CA certificate is copied to
   ``/etc/univention/ssl/ucsCA/CAcert.pem`` inside the container.

-  The Docker host UCS certificate is copied to
   ``/etc/univention/ssl/docker-host-certificate/{cert.perm,private.key}``
   and
   ``/etc/univention/ssl/$FQDN_DOCKER_HOST/{cert.perm,private.key}``.

Every app can define a update_certificates script. In the app provider
portal it can be added on the tab Advanced in the section Certificates.

Example:

.. code:: sh

   #!/bin/bash
   # cat the UCS root CA to the app's root CA chain
   cat /etc/univention/ssl/ucsCA/CAcert.pem >> /opt/my-app/ca-bundle.crt
   service my-app-daemon restart
               

The script has to be uploaded via the upload API (section :ref:`App Provider
Portal upload interface <upload-interface>`). The script should be
written locally and then uploaded with the following command:

.. code:: sh

   ./univention-appcenter-control upload --username $your-username 5.0/myapp=1.0 update_certificates
               

Mail integration
----------------

|UCSUCS| (UCS) provides a complete mailstack with the Mailstack app in the
App Center. It includes Postfix as *MTA* for SMTP and Dovecot for IMAP.
If the app relies on an existing mail infrastructure, it is one option
to use the mailstack app and require its installation in the UCS domain.
This can be configured for the app in the App Provider portal on the
Version tab in the section Required apps by adding the Mailserver app
and setting ``Installed in domain``. With this configuration the App
Center on the system administrator's UCS system will check, if the
*Mailserver* app is installed somewhere in the domain and asks the
administrator to install it accordingly.

Next the app needs to be configured to use the UCS SMTP and IMAP
servers. This is done in the Join Script (see :ref:`Join
script <installation:joinscript>`). The following snippet gives an
example what should be included in the Join Script:

.. code:: sh

   ...
   eval "$(univention-config-registry shell)"
   ...
   # use the first IMAP server as smtp and imap server
   mailserver="$(univention-ldapsearch -LLL '(univentionService=IMA)' cn |
   sed -ne 's/^cn: "//p;T;q')"
   if [ -n "$mailserver" ]; then
     mailserver="$mailserver.$domainname"

     # for Docker Apps the helper script joinscript_run_in_container
     # can be used to run commands in the container
     . /usr/share/univention-appcenter/joinscripthelper.sh
     joinscript_run_in_container my-app-setup --config imap="$mailserver"
     joinscript_run_in_container my-app-setup --config smtp="$mailserver"
     joinscript_run_in_container my-app-setup --config sieve="$mailserver"
   fi
   ...
               

The snipped searches the UCS LDAP directory for the host with the
service IMAP and sets the FQDN of this host as IMAP, SMTP and SIEVE
server for the app. This is a good default and may not be correct for
some setups.

The best practice mail settings when the UCS mailstack is used, are the
following.

IMAP:

-  TLS

-  Port 143

-  Authentication is possible for domain users with a primary mail
   address.

-  The user's uid or the primary mail address are both valid for
   authentication.

SMTP:

-  TLS

-  Port 587 (submission) for authentication

-  Mechanism Login or Mechanism Plain

.. _mail-integration:with-docker-apps:

Provide mail with Docker Apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the intended app it may be necessary to provide SMTP and IMAP with a
custom setup for the app. To provide SMTP and/or IMAP services in a
Docker app, these services have to be stopped on the Docker host. This
can be done in the app's preinst Docker script, see :ref:`Script called
before installation to verify that App may be
installed <installation:preinst>`. Example:

.. code:: sh

   #!/bin/bash

   # stop imap/smtp on docker host
   systemctl stop postfix dovecot
   ucr set postfix/autostart=no dovecot/autostart=no
                       

To map SMTP and/or IMAP ports from the container to the host to be able
to use the Docker host as IMAP/SMTP server exclusive ports for the
container have to be set to the relevant ports (e.g. 110, 143, 993, 995,
587, 25, 465, 4190 for pop3(s), imap(s), smtp(s), submission and sieve).
See :ref:`Ports <create-app-with-docker:ports>` on how to set an exclusive
port.

Firewall exceptions for these ports are create automatically.

Best practice is to at least map the IMAP data store to the Docker host
to provide a separation of data and container (important for migration
to Docker and Docker image updates). See :ref:`Persistent data with
volumes <create-app-with-docker:volumes>`.

.. _mail-integration:local-mail-docker-host:

Use local mail on Docker host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With a stopped Postfix on the Docker host, mail can no longer be
delivered locally. If that is a problem, the following setup can help.

Install the extremely simple MTA ssmtp and configure this MTA to use the
localhost (our Docker container is listening on localhost:25).

.. code:: sh

   univention-install --yes ssmtp
   # add mailhub=localhost:25 in to /etc/ssmtp/ssmtp.conf
                   

Now configure Postfix in the Docker container to deliver mails from the
Docker host locally by adding the FQDN of the Docker host to
mydestination:

.. code:: sh

   ucr set mail/postfix/mydestination="\$myhostname, localhost.\$mydomain, localhost, $DOCKER_HOST_NAME"
                   

.. _subdomains:

Subdomains / dedicated FQDN for an App
--------------------------------------

There may be reasons why an App needs to have its own FQDN within the
UCS domain. Some Apps may not be able to configure a web interface that
integrates well into the default Apache sites of UCS (see :ref:`Web
interface <create-app-with-docker:web-interface>`).

To avoid naming collisions, the App's FQDN should reference the Docker
Host's FQDN, e.g, ``myapp.ucs-primary.domain.tld``. UCS can do the
following to allow this scenario to work as smooth as possible:

-  Add a dedicated FQDN for the App and make it known to the internal
   DNS. That means that the new FQDN is an alias for the actual FQDN of
   the Docker host.

-  Generate a certificate for this FQDN. Technically, a wildcard
   certificate is created.

-  Generate a virtual host for Apache with that new FQDN. Thus, requests
   to that FQDN will be handled by the *VHost*. The skeleton
   configuration can be easily extended by writing a configuration file
   that is then included in the *VHost* entry.

For this to work, this snippet can be used in the join script (:ref:`Join
script <installation:joinscript>`):

.. code:: sh

   univention-add-vhost \
       "myapp.$(ucr get hostname).$(ucr get domainname)" 443 \
       --conffile /var/lib/univention-appcenter/apps/myapp/data/apache.conf \
       "$@"  # "$@" is used to pass credentials
   # write the apache.conf, maybe by using the App Settings
   systemctl reload apache2
   nscd -i hosts  # only needed if the new fqdn should be used immediately by the system
   systemctl reload bind9  # same here
                   

This will create the following entry in
``/etc/apache2/sites-available/univention-vhosts.conf``

.. code:: sh

   # Virtual Host for myapp.ucs-primary.domain.tld/443
   <IfModule mod_ssl.c>
   <VirtualHost *:443>
       ServerName myapp.ucs-primary.domain.tld
       IncludeOptional /var/lib/univention-appcenter/apps/myapp/data/apache.con[f]
       SSLEngine on
       SSLProxyEngine on
       SSLProxyCheckPeerCN off
       SSLProxyCheckPeerName off
       SSLProxyCheckPeerExpire off

       SSLCertificateFile /etc/univention/ssl/*.ucs-primary.domain.tld/cert.pem
       SSLCertificateKeyFile /etc/univention/ssl/*.ucs-primary.domain.tld/private.key
       SSLCACertificateFile /etc/univention/ssl/ucsCA/CAcert.pem
   </VirtualHost>
   </IfModule>
               

..

.. note::

   Although this seems convenient for some Apps, this feature creates an
   *internal* name. It may still be inconvenient for testers that run
   UCS in a virtual environment where their browser is not part of UCS'
   DNS.

.. warning::

   This method may not work in the "AD member mode". There, a Windows
   Domaincontroller is the leading system and provides the DNS. The DNS
   alias has to be added by the Admin manually there as our script
   cannot add it for them.

Firewall
--------

This section describes how the local Univention Firewall based on
iptables is changed by apps and how it can be customized. Docker
containers have access to the Docker host. And the Docker containers can
be made available for external clients with Ports redirection settings
(see :ref:`Ports <create-app-with-docker:ports>`).

If MariaDB or PostgreSQL are used as database, those ports will be
opened automatically for the Docker container (section
:ref:`Database <create-app-with-docker:database>`).

Every app can provide additional custom rules to open required ports.
This can be done in the join script (section :ref:`Join
script <installation:joinscript>`). In the example the port 6644 is
opened for TCP and UDP:

::

   univention-config-registry set \
       "security/packetfilter/package/$APP/tcp/6644/all=ACCEPT" \
       "security/packetfilter/package/$APP/tcp/6644/all/en=$APP" \
       "security/packetfilter/package/$APP/udp/6644/all=ACCEPT" \
       "security/packetfilter/package/$APP/udp/6644/all/en=$APP"

   systemctl try-restart univention-firewall
           

Please also add corresponding ``ucr unset`` commands in the unjoin
script so that the firewall rules will be removed when the app is
removed from the system (section :ref:`Unjoin
script <uninstallation:unjoin>`).

