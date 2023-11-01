.. _software:

*******************
Software management
*******************

This section describes the differences of UCS with respect to software
management. In this section, the term *software management* refers to the
lifecycle of software on a computer system, such as installing software on a
computers system, updating, and removing existing software.

As an enterprise Linux distribution, |UCS| has defined maintenance cycles for
its version levels and uses terms such as *errata updates* or
*patch level releases*.

.. seealso::

   :ref:`uv-manual:computers-differentiation-of-update-variants-ucs-versions` in
   :cite:t:`ucs-manual`.

.. _software-default:

Default software on UCS
=======================

Univention uses many open source products and adapts them to |UCS|, such as
:program:`OpenLDAP`, :program:`OpenSSL`, :program:`Samba`, :program:`Apache HTTP
Server`. The product capability relies on these products. Replacing the existing
packages with the personal favorite breaks UCS. For example, using
:program:`nginx` instead of the |UCS| default :program:`Apache HTTP Server`.

.. _rule-2:

.. admonition:: Rule #2

   Use the standard software packages that |UCS| installs to provide core product
   capabilities.

   Don't replace these software packages with software of your own personal
   taste.

.. _software-repositories-packages:

Software repositories and packages
==================================

As a Linux distribution based on Debian GNU/Linux, UCS also uses software
packages in the deb file format and the corresponding package repositories.
Univention provides and maintains software packages in package repositories. The
packages have two different maintenance statuses: *maintained* and
*unmaintained*.

.. seealso::

   * :ref:`uv-architecture:positioning-packages` in :cite:t:`ucs-architecture`.

   * :ref:`uv-manual:software-config-repo` in :cite:t:`ucs-manual`.

.. _software-commands:

Commands for software management
================================

To install, update, and remove software packages from a Debian GNU/Linux system,
the Debian Project provides the commands :command:`apt` for interaction with the
package manager and :command:`apt-get` for non-interactive interaction. For
graphical interaction, there are tools such as :program:`aptitude` and
:program:`synaptic`. As a Debian or Ubuntu administrator you are familiar with
these tools.

|UCS| provides the following command line tools as wrappers around
:command:`apt-get`:

:command:`univention-update`
   to update the package cache on a UCS system.

:command:`univention-install`
   to install software packages from a software repository on UCS.

:command:`univention-upgrade`
   to update installed software packages on a UCS system, for example errata
   updates or patch level releases.

:command:`univention-remove`
   to remove installed software packages from UCS.

:command:`univention-app`
   to install, update, or remove apps in the App Center on UCS.

.. _rule-3:

.. admonition:: Rule #3

   Use the :command:`univention-*` tools to perform actions for installing,
   updating and removing software packages and apps on UCS.

In contrast to :command:`apt` and :command:`apt-get`, the :command:`univention-*`
commands take care of the following additional aspects of software management on
UCS:

#. Not all administrators run :command:`apt update` before installing software.
   :command:`univention-install` always updates the software package cache
   before installing software. This ensures that the package manager installs
   the latest stable software version.

#. :command:`univention-install` ensures to apply configuration settings for
   examples from :ref:`UCR variables <system>` or join scripts.

   For example, when installing :program:`Postfix` with :command:`apt`, the
   package's standard wizard asks for the type of the mail system, such as
   *Internet Site*, *Internet with smarthost*, *Satellite system*, or *Local
   only*. :command:`univention-install` doesn't run the wizard. Instead, it
   applies the relevant system configuration settings so that the mail server
   works after the installation and is ready for your adjustments, if required.

   .. TODO : Add reference to join script chapter.

#. The installation of meta packages ensures that the package manager uses
   UCS mechanisms during the installation, such as the correct configuration of
   the software package and information storage in the domain.

.. seealso::

   For further information about the mentioned commands, see the following
   sections in :cite:t:`ucs-manual`:

   * :ref:`uv-manual:computers-installation-removal-of-individual-packages-in-the-command-line`

   * :ref:`uv-manual:software-appcenter`

.. _software-updates:

Automatic software updates
==========================

|UCS| uses policies to define automatic software updates for systems in a
domain.

.. seealso::

   For more information, see the following sections in
   :cite:t:`ucs-manual`:

   * :ref:`uv-manual:computers-softwaremanagement-release-policy`

   * :ref:`uv-manual:computers-softwaremanagement-maintenance-policy`

Beyond software packages
========================

In addition to the well-known software packages, Univention also distributes
software as apps through Univention App Center. Apps consist of the software and
its integration into |UCS| and the domain. For example, to install apps such as
UCS components such as :program:`Active Directory-compatible Domain
Controller` or third-party software such as :program:`Nextcloud` or
:program:`ownCloud`, you must use the App Center, either the corresponding UMC
module or the :command:`univention-app` command. Most apps use Docker images and
offer a ready-to-use integration with UCS.

.. seealso::

   For more information, see the following resources:

   * :ref:`uv-manual:software-appcenter` in :cite:t:`ucs-manual`:
   * :ref:`uv-architecture:univention-app-ecosystem` in :cite:t:`ucs-architecture`:
   * `Univention App Center Catalog <https://www.univention.com/products/app-catalog/>`_

.. _software-third-party:

Third party sources
===================

As a Debian or Ubuntu administrator you know about the ability to add
third-party software repositories to install additional software on your system.

You can also add third-party repositories to |UCS| by editing the sources lists
or adding files to :file:`/etc/apt/sources.list.d`. While this is possible, it's
not recommended. Be aware of the possible negative consequences, such as
breaking existing services.

For example, adding PHP packages from another PHP repository interferes with the
existing PHP packages and may negatively affect other software from the UCS
software repository that relies on the default PHP version in UCS. Product tests
only cover software packages from the Univention software repository.

With regard to additional Python packages, don't install packages through
:command:`pip` into your system-wide Python environment, but into the virtual
environment instead. See :py:mod:`venv - Creation of virtual environments
<python:venv>`

.. _rule-4:

.. admonition:: Rule #4

   Before installing software packages from third-party sources:

   #. Always verify the App Center and the standard Univention software
      repositories, if the software is already available there.

   #. Make sure that the packages don't overwrite existing packages.

   #. Use :command:`pip` only in virtual Python environments.
