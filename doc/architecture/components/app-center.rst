.. SPDX-FileCopyrightText: 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _component-app-center:

App Center
==========

Univention App Center is one of the most important parts of |UCS|. It's
responsible for the lifecycle management of UCS components and third party
applications that add enterprise software to the UCS domain. The App Center
simplifies the installation and integration of software with UCS. In this
respect, the App Center is similar in principle to the app stores on mobile
platforms, with the difference that it applies to the server infrastructure.

Apps is short for software applications. Univention offers components for UCS as
apps. And third party vendors, so-called app providers, offer software solutions
as apps. Apps consist of software, integration with UCS and metadata, such as
texts and logos for presentation. A central idea of the apps is the tight
integration with UCS, especially the integration with identity management. For
more information about app artifacts, refer to :ref:`app-center-ecosystem-apps`.

Like many other product components, administrators interact with the App Center
either through the web based management system or a terminal as shown in
:numref:`component-app-center-architecture-component`.

.. _component-app-center-architecture-component:

.. figure:: /images/App-Center-architecture-component.*
   :width: 600 px

   Architecture overview of the App Center

Abstractly speaking, the application service *App Center Service* offers a web
interface through *HTTP/HTTPS* and a command line interface through *Terminal /
SSH*.

The following list demarcates the App Center from its capabilities. The App
Center isn't:

* a tool to distribute software specific to customers or projects.

* a solution for every use case. It has limitations for example in large
  environments that require setups for a cluster or load balancing.

Think of the App Center as a global entity in the UCS domain. The App Center
addresses all UCS systems. Administrators can view and install any available
app.

.. admonition:: Continue reading

   :ref:`services-app-center`
      for the next detail level with description of the architecture of the App
      Center.

.. seealso::

   :ref:`univention-app-ecosystem`
      for information about the Univention app ecosystem.

   :ref:`software-appcenter`
      for information for administrators about the App Center in
      :cite:t:`ucs-manual`

   :external+uv-app-center:doc:`Univention App Center for App Providers <index>`
      for information about how to develop apps for Univention App Center in
      :cite:t:`ucs-app-center`
