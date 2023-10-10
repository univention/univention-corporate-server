.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-umc:

UMC - Univention Management Console
===================================

.. index:: umc
   see: univention management console; umc

This section describes the technical architecture of the Univention Management
Console (UMC). For a general overview and its relation to system management,
refer to :ref:`component-system-management`.

You find the source code at the following locations:

* :uv:src:`management/univention-management-console/`

* Web interface presentation layer at :uv:src:`management/univention-web/`

* Packages with UMC modules usually include a :file:`umc` directory, for example:

  * :uv:src:`base/univention-quota/umc/`
  * :uv:src:`base/univention-system-setup/umc/`
  * :uv:src:`base/univention-updater/umc/`
  * :uv:src:`management/univention-appcenter/umc/`
  * :uv:src:`management/univention-management-console-module-join/umc/`
  * :uv:src:`management/univention-management-console-module-adtakeover/umc/`
  * :uv:src:`management/univention-management-console-module-diagnostic/umc/`
  * :uv:src:`management/univention-management-console-module-ipchange/umc/`
  * :uv:src:`management/univention-management-console-module-reboot/umc/`
  * :uv:src:`management/univention-management-console-module-services/umc/`
  * :uv:src:`management/univention-management-console-module-top/umc/`
  * :uv:src:`management/univention-management-console-module-ucr/umc/`
  * :uv:src:`management/univention-management-console-module-udm/umc/`
  * :uv:src:`management/univention-management-console-module-welcome/umc/`
  * :uv:src:`management/univention-self-service/umc/`
  * :uv:src:`management/univention-server-overview/umc/`
  * :uv:src:`management/univention-system-info/umc/`
  * :uv:src:`saml/univention-saml/umc/`
  * :uv:src:`services/univention-ad-connector/umc/`
  * :uv:src:`services/univention-admin-diary/umc/`
  * :uv:src:`services/univention-pkgdb/umc/`
  * :uv:src:`services/univention-printserver/umc/`

Every UCS system installs |UMC| and its dependencies per default. |UMC| consists
of the *UMC frontend* and the *UMC backend*.
:numref:`services-umc-architecture-simplified-model` shows the simplified
architecture of Univention Management Console and the description thereafter.

.. index::
   single: umc; architecture
   single: model; umc

.. _services-umc-architecture-simplified-model:

.. figure:: /images/UMC-architecture-simple.*
   :width: 350 px

   Architecture overview of Univention Management Console

.. index::
   single: umc; client
   single: umc; frontend
   single: umc; web frontend

The *UMC frontend* has the following items:

* *UMC web frontend*
* *UMC client*

.. index:: ! umc modules
   pair: umc; reverse proxy
   pair: umc; static http server
   single: umc; backend
   single: umc; modules
   single: umc; server

The *UMC backend* has the following items:

* *Static HTTP server*
* *Reverse proxy*
* *UMC server*
* *UMC modules*

The user facing parts of the *UMC frontend* are the *UMC web frontend* and the
*UMC client*. *Reverse proxy* handle and transform the
requests and pass them to the *UMC server* at the backend.

.. _services-umc-communication:

UMC communication
-----------------

.. index::
   single: umc; communication
   single: umc; terminal
   single: model; umc communication

This section focuses on the communication within |UMC|.
:numref:`services-umc-architecture-communication-model` shows the architecture
with the communication interfaces *HTTP/HTTPS*, *HTTP*, *Terminal/SSH*.
The following sections describe the interfaces.

.. _services-umc-architecture-communication-model:

.. figure:: /images/UMC-architecture-communication.*
   :width: 350 px

   Architecture of Univention Management Console with communication interfaces

.. _services-umc-https:

HTTP/HTTPS in UMC
~~~~~~~~~~~~~~~~~

.. index::
   pair: umc; http
   pair: umc; https

The user interacts with the *UMC web frontend* in their web browser. The *UMC
web frontend* communicates through *HTTP/HTTPS* with the *UMC backend*. The
*Reverse proxy* receives requests, handles SSL/TLS, and forwards the requests
through *HTTP* to the *UMC server*.

.. _services-umc-terminal:

Terminal and SSH in UMC
~~~~~~~~~~~~~~~~~~~~~~~

.. index:: ! umc; client
   single: umc; command line
   single: umc; server
   single: umc; web frontend

The *UMC client* communicates with *UMC backend* through ``HTTPS``. Administrators
use UMC through the *UMC web frontend* or through specific command-line tools.

.. caution::

   Although |UMC| offers a *Command line* through *Terminal/SSH*, only software
   developers use the interface for example for software testing. Interaction
   with the interface requires knowledge about the internals of *UMC modules*.


.. _services-umc-authentication:

Authentication
--------------

.. index::
   pair: umc; authentication
   single: umc; saml
   single: authentication; basic http
   single: authentication; form-based login
   single: authentication; saml
   single: umc; server
   single: saml; service provider role
   single: saml; umc authentication

|UMC| provides the web and authentication interface of the UCS management
system. Users authenticate through a regular form-based login, basic HTTP
authentication or |SAML|.

In UMC, the *UMC server* implements |SAML| in the *SAML service provider*
role. The *UMC server* considers SAML authenticated users as authenticated.

.. TODO : Activate section, once SAML is ready:
   For details about |SAML| in UCS, refer to :ref:`services-authentication-saml`.

The *UMC server* handles user authentication as shown in
:numref:`services-umc-authentication-chain`.

.. index:: umc; authentication successful
   single: authentication; successful

Successful authentication
   *UMC server* creates a session and returns a session cookie.

.. index:: umc; authentication unsuccessful
   single: authentication; unsuccessful

Unsuccessful authentication
   *UMC server* denies the connection and answers with a
   denied request towards the user. The reasons can be manifold, for example:

   * Wrong username and password combination
   * Disabled user account
   * Expired password
   * Locked account because of too many failed login attempts

.. index::
   single: umc; authentication chain

.. _services-umc-authentication-chain:

.. figure:: /images/UMC-authentication.*

   Authentication chain in UMC

The *UMC server* uses the |PAM| stack on UCS to validate and authenticate users
for usual login and for |SAML| authentication. *UMC server* evaluates |ACL|\ s
to grant or deny the usage of UMC modules. To find the user object for the
authenticating user, *UMC server* runs an LDAP search for the username. It also
allows to authenticate users with their email address. Furthermore, |PAM|
recognizes deactivated user accounts, expired passwords, and allows to change an
expired password during sign-in.


.. seealso::

   Administrators, refer to :cite:t:`ucs-manual`:

   :ref:`users-management-table-account`
      for information about deactivated and expired user accounts

   :ref:`users-faillog`
      for information about failed login attempts and how UCS handles them in
      Samba, PAM and OpenLDAP

.. _services-umc-back-end:

UMC backend
-----------

.. index:: ! umc; backend
   single: umc; backend architecture
   single: umc; module processes
   single: IPC socket
   single: umcp; umc backend

The *UMC backend* consists of the following items as shown in
:numref:`services-umc-architecture-simplified-model`:

* *Reverse proxy*
* *UMC server*
* several *UMC modules*

In :numref:`services-umc-backend-model` you see the *Reverse proxy* you already
know from :numref:`services-umc-architecture-simplified-model`. In fact, the web
server offering the *Reverse proxy* consists of more parts.

.. index:: umc; backend model
   single: model; umc backend

.. _services-umc-backend-model:

.. figure:: /images/UMC-back-end.*
   :width: 650 px

   Parts of the *UMC backend*

.. index:: ! umc; static http server
   single: technology; apache http server

Static HTTP server
   First is the web server realized by :program:`Apache HTTP server`. The web
   server provides the *Static HTTP server* that delivers the static files for
   the *UMC web frontend*. And the *Static HTTP server* responds with important
   HTTP headers for caching rules of the static files and security related
   headers like for example `content security policy <mdn-csp_>`_.

.. index:: ! umc; reverse proxy
   single: apache; mod_proxy
   single: apache; http server

Reverse proxy
   Second is the reverse proxy capability from the :program:`Apache HTTP server`
   with the reverse proxy module (*mod_proxy*). The *Reverse proxy* also responds
   with important HTTP headers similar to the *Static HTTP server*.

   The *Reverse proxy* redirects the following URI paths to the *UMC web
   server*:

   * ``/univention/set/.*`` as regular expression
   * ``/univention/auth``
   * ``/univention/logout``
   * ``/univention/saml/.*`` as regular expression
   * ``/univention/command/.*`` as regular expression
   * ``/univention/upload/.*`` as regular expression
   * ``/univention/get/.*`` as regular expression

.. index:: ! umc; server
   single: technology; tornado
   single: umc server

UMC server
   Further down the chain is the *UMC server* realized by
   :program:`Tornado`, that only allows connections from the *Reverse proxy*.
   For example, it provides session management for signed-in users.

   The *UMC server* accepts requests with ``HTTP``. For example, the *UMC client*
   uses it as connection endpoint. When a ``HTTP`` request
   reaches the *UMC server*, the *UMC server* maps the request to a dedicated
   UMC module depending on the URL and answers the request
   accordingly. The *UMC server* opens an |IPC| socket to the UMC module and
   they talk ``HTTP``. It handles some requests directly, for example ``get/`` and
   ``set/``, and takes care of authentication and the language setting for the
   web content.

UMC module processes
   UMC modules extend UCS with capability. For the description, refer to
   :ref:`services-umc-modules`.

.. seealso::

   `Apache HTTP server project <apache-httpd_>`_
      for the website of the Apache HTTP server project

   `Tornado <tornado_>`_
      for the website of the *Tornado* project

.. _services-umc-web-front-end:

UMC web frontend
----------------

.. index:: ! umc; web frontend
   single: technology; dojo toolkit
   single: dojo toolkit
   single: technology; bootstrap
   single: bootstrap

The *UMC web frontend* is responsible for the presentation layer of |UMC| and
runs in the user's web browser. It uses the modular JavaScript framework
:program:`Dojo Toolkit` to create dynamic widgets. And it uses the
:program:`Bootstrap` CSS framework for responsive designed web pages.

:numref:`services-umc-web-front-end-model` provides a detailed view on the model
of the *UMC web frontend*.

.. index::
   single: umc; web frontend model
   single: model; umc web frontend

.. _services-umc-web-front-end-model:

.. figure:: /images/UMC-web-front-end.*
   :width: 550 px

   Model for UMC web frontend

The *UMC web frontend* consists of static files for JavaScript, HTML and CSS.
The *UMC backend* sends the static files to the user's web browser, where the
web browser presents UMC as a web application. The following packages from
:uv:src:`management/univention-web/` contain the artifacts for the web front
user interface:

.. index::
   pair: univention-web-js; umc
   pair: univention-web-styles; umc
   pair: univention-management-console-frontend; umc

:file:`univention-web-js`
   Contains the ready-to-use JavaScript files built with :program:`Dojo
   Toolkit`.

:file:`univention-web-styles`
   Contains the ready-to-use CSS files for the web design including the
   graphical theme built with :program:`Bootstrap`.

:file:`univention-management-console-frontend`
   Contains the HTML files for the *UMC web frontend*. More packages like
   :file:`univention-server-overview`,
   :file:`univention-management-console-login`, :file:`univention-system-setup`,
   :file:`univention-portal` and others also contain HTML files for the *UCS
   management system*.

.. seealso::

   `Dojo Toolkit <dojo-toolkit_>`_
      Modular JavaScript framework

   `Bootstrap <bootstrap_>`_
      Powerful, extensible, and feature-packed front end toolkit

.. _services-umc-modules:

UMC modules
-----------

.. index:: ! umc; modules
   single: model; umc modules
   single: umc; modules architecture
   single: umc; server

This section covers *UMC modules*. For the context of *UMC modules*, refer to
:ref:`services-umc-back-end`.

UMC modules extend UCS with capability. Each UMC module defines its command
behavior with a Python implementation and its web frontend presentation with
JavaScript as shown in :numref:`services-umc-module-architecture-model`.

.. _services-umc-module-architecture-model:

.. figure:: /images/UMC-module-architecture.*
   :width: 500 px

   Architecture of a UMC module

Depending on the system role, UCS already installs UMC modules per default
during installation. Such modules are for example the *App Center*, or *Package
Management*. Furthermore, apps from the App Center can also extend |UMC| with
additional modules, for example the *OX License Manager* or *OpenVPN4UCS*.

Every UMC module runs its own module process per user session on UCS with the
user permission according to the requesting user. The encapsulation with
separate processes ensures that UMC modules don't interfere with each other. One
disadvantage is the additional memory consumption of every UMC module process.

UMC module processes don't run continually. After an idle time of ten minutes
and if no open requests exist and no additional requests came in, module
processes stop. The *UMC server* checks for running UMC module processes for
every request. If the requested process doesn't run, the *UMC server* starts the
UMC module process.

.. tip::

   Use :envvar:`umc/module/timeout` to configure the idle time for the UMC module
   processes. The default value is 10 minutes.

.. seealso::

   :ref:`Development and packaging of UMC modules <uv-dev-ref:umc-module>`
      for information about development and packaging for UMC modules in
      :cite:t:`developer-reference`
