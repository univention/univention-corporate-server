.. _system:

********************
System configuration
********************

This section covers the differences of UCS in the area of system configuration.
The term *system configuration* in the context of this section refers to
controlling the behavior of a system and its services through configuration
files.

Administrators typically configure Linux operating systems using text-based
configuration files. Debian GNU/Linux and Ubuntu are no exception to this
principle. The advantage of a text-based configuration format is that it
requires no need for extra tools or knowledge other than a text editor and a
documentation of the configuration syntax. Text-based configuration is also
useful for configuration management and infrastructure as code software such as
:program:`Ansible` that allow administrators to configure multiple systems.

|UCS|, being a derivative of Debian GNU/Linux and thus a Linux operating system,
is no exception to this principle. The services on a UCS system use their
familiar text-based configuration files. As an administrator with Linux
know-how, it's natural to manually edit the configuration with a text editor and
adapt the settings of a service to the needs of their environment.

.. _system-templates-for-configuration:

Template system for configuration files
=======================================

When it comes to manually editing configuration files, UCS is different from
other Linux distributions. UCS automatically generates most configuration files
from text-based file templates and a key-value-based variable store. Univention
calls this capability *Univention Configuration Registry (UCR)*.

.. seealso::

   For a detailed elaboration, see the following sections in
   :cite:t:`ucs-architecture`:

   * :ref:`component-configuration-registry`
   * :ref:`services-ucr`

|UCS| uses |UCR| for the following non exhaustive list of benefits:

* Single setting values can apply to multiple configuration files. UCR ensures
  configuration consistency for services affected on a system.

* The majority of software packages on UCS use |UCR| for their configuration.

* Avoid configuration errors resulting from an invalid configuration setting
  syntax.

* Logging of changes to UCR variables.

You can recognize configuration files controlled by UCR by the presence of a
header at the beginning of the file, as shown in :numref:`ucr-header`. The
header lists the template files used to generate the configuration file:

.. code-block::
   :caption: Header in configuration files under control of |UCR|
   :name: ucr-header

   # Warning: This file is auto-generated and might be overwritten by
   #          univention-config-registry.
   #          Please edit the following file(s) instead:

.. seealso::

   For detailed information about how to use |UCR|, see the following sections
   in :cite:t:`ucs-manual`:

   * :ref:`uv-manual:computers-administration-of-local-system-configuration-with-univention-configuration-registry`

   * :ref:`uv-manual:computers-using-the-command-line-front-end`

   * :ref:`uv-manual:ucr-templates-extend`

.. _system-listener:

Listener modules writing configuration files
============================================

As an operating system utilizing a :ref:`uv-architecture:concept-domain` and a
:ref:`uv-architecture:concept-replication`, the so-called *Listener-/Notifier
mechanism* also generates configuration files based on configuration data in the
domain database and |UCR|.

Changes to |UCR| don't trigger a regeneration of those files. Changes to related
objects in the domain database, so-called UDM objects, trigger a regeneration.
And a command to re-synchronize a listener module also regenerates affected
files.

.. important::

   Unfortunately, listener modules that generate configuration files don't add a
   header with a warning to configuration files. For a status, see :uv:bug:`56790`.

.. seealso::

   For more information, see the following resources in :cite:t:`ucs-manual`:

   * :ref:`uv-manual:domain-listener-notifier`

   * :ref:`uv-manual:domain-listener-notifier-erroranalysis-reinit`

   For more information about the concepts, see the following resources in
   :cite:t:`ucs-architecture`:

   * :ref:`uv-architecture:concept-domain`

   * :ref:`uv-architecture:concept-replication`

.. _system-result-manual-edit:

Consequences of manual configuration file editing
=================================================

Editing configuration files manually, as you practice it for other Linux
distributions, may bring you closer to your goal. At first glance, you have a
good feeling, because the configuration works as expected. The feeling can turn
into frustration, because the carefully handmade configuration vanished.
Software package updates and installation of additional software trigger UCR to
regenerate configuration files and therefore overwriting custom changes.
Restarting the service, or rebooting the system, activate the changes in the
configuration files.

Sometimes the reasons for problems are hard to find. Any run of |UCR| can affect
the configuration, overwrites manual changes, and can cause additional effort
for analysis and repair.

The negative consequences range from small effects such as the return to the
default behavior of a service up to key services not running anymore at all. For
example, the LDAP server refuses to start and prevents users from sign-in to
their environment and preventing them from doing their daily work.

This short outline brings use to one rule. Applying it can safe you a lot of
frustration, efforts, and headaches:

.. _rule-1:

.. admonition:: Rule #1

   Don't manually edit configuration files that are under control of |UCR| or
   directory listener modules.

.. _system-customize-configuration:

Customize configuration
=======================

Nevertheless, UCS is an open system and wants to enable administrators to
customize it to their needs. To avoid problems caused by ignoring |UCR|, use it
to your advantage.

#. Take existing |UCR| variables and the |UCR| system to customize a UCS system
   to your needs.

To add a custom configuration, not covered by existing UCR variables, use one of
the following possibilities:

2. :ref:`ucr-templates-extend` and customize it to your needs.

   However, keep in mind that the template file is under the control of a
   software package. After a package update you may need to manually merge your
   customization with the update that Univention provides for the package. As
   long as the merge isn't resolved, the affected service may not work at all.

#. Use local configuration possibilities such as :file:`local.conf` files or local
   configuration directories.

   The local configuration possibilities strongly depend on the service you have
   in mind and what their configuration options offer at all.

   Examples:

   * The Apache web server

   * The print service offers a local configuration, see :ref:`uv-manual:print-services-configuration`.

   * The :program:`Samba` domain services

   * The IMAP server :program:`Dovecot`

   * File and print shares

.. seealso::

   See the following resources in :cite:t:`ucs-manual`

   * :ref:`computers-administration-of-local-system-configuration-with-univention-configuration-registry`

   * :ref:`ucr-templates-extend`
