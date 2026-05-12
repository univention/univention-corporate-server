.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-ucr:

Configure the local system with Univention Configuration Registry
=================================================================

Univention Configuration Registry (UCR) is a key-value store for system settings.
Services and programs read these settings
to configure themselves automatically.
UCR runs on every Nubus for UCS system.

UCR provides the following advantages:

* UCR manages configuration files without requiring direct edits.
  This avoids errors from invalid syntax or incorrect values.

* UCR provides a single interface for editing settings,
  regardless of the format used by the underlying configuration files.

* UCR variables are independent of the configuration file format.
  If a package switches to a different format,
  you update the UCR template instead of converting the file.

* When a variable changes,
  UCR automatically regenerates all configuration files that use it.

To manage UCR variables:

* On the command line,
  run :command:`univention-config-registry`.

* In the *Management UI*,
  open the *Univention Configuration Registry* management module.

When you install Nubus for UCS,
you provide the initial settings for packages that use UCR.
Afterward, the system automatically sets hundreds of UCR variables.

You can also use UCR variables in shell scripts
to access system settings.

Variable names use forward slashes to separate parts,
for example :envvar:`ldap/base` or :envvar:`mail/relayhost`.
UCR variables whose names begin with ``ldap`` control the local LDAP service.

Each UCR variable describes what it does.

.. caution::

   If UCR manages a configuration file through a template,
   edit the template instead of the configuration file directly.
   UCR overwrites any changes you make to the file
   the next time UCR regenerates the file from the template.
   For details,
   see :ref:`system-administration-ucr-templates`.

.. _system-administration-ucr-umc:

Manage UCR variables in the Management UI
-----------------------------------------

Use the *Univention Configuration Registry* management module
to search, edit, and delete variables.

The start page shows a search box and a list of variable categories.
For example, you can browse all LDAP-specific settings in one view,
see :numref:`system-administration-ucr-umc-figure`.

To manage UCR variables in the management module,
your account must belong to the ``Domain Admins`` group.

.. _system-administration-ucr-umc-figure:

.. figure:: /images/ucr.*
   :alt: Managing UCR variables in the Management UI

   Managing UCR variables in the *Management UI*

.. _system-administration-ucr-umc-manage:

Manage a UCR variable
~~~~~~~~~~~~~~~~~~~~~

To manage UCR variables in the management module:

#. In the :guilabel:`Search attribute` field,
   filter variables by name, value, or description.

#. In the results table,
   confirm the variable names and values match your expectations.

#. To view a brief description of a variable,
   point to its name to open a tooltip.

#. To view the full details of a variable,
   select it.

#. To edit a variable, click its name.

#. To delete a variable, right-click it and select :guilabel:`Delete`.

.. _system-administration-ucr-umc-create:

Create a UCR variable
~~~~~~~~~~~~~~~~~~~~~

To create a UCR variable:

#. Click :guilabel:`Add`.

#. Enter a name in the :guilabel:`Variable` field
   and a value in the :guilabel:`Value` field.

#. Click :guilabel:`Save`.

.. _system-administration-ucr-command-line:

Manage UCR variables on the command line
----------------------------------------

.. program:: ucr

You must have root access to run UCR commands on the command line.

Run UCR commands with :command:`univention-config-registry`.
You can also use the short command :command:`ucr`.

.. _system-administration-ucr-command-line-query:

Query a UCR variable
~~~~~~~~~~~~~~~~~~~~

.. Note to editors: The ``.. option::`` directive is used here for sub-commands
   (get, dump, set, search, unset, commit, shell) rather than flags.
   This is an intentional pragmatic choice because ``.. option::`` generates
   cross-referenceable targets through ``:option:``.

.. option:: get

   Use the :option:`get` sub-command to query a single UCR variable.
   :numref:`ucr-get-example` shows an example.

   .. code-block:: console
      :caption: Query a UCR variable with :option:`get`
      :name: ucr-get-example

      $ univention-config-registry get ldap/server/ip

.. _system-administration-ucr-command-line-dump:

Display all UCR variables
~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: dump

   Use the :option:`dump` sub-command to display all variables that have a value assigned.
   :numref:`ucr-dump-example` shows an example.

   .. code-block:: console
      :caption: Display all UCR variables with :option:`dump`
      :name: ucr-dump-example

      $ univention-config-registry dump

.. _system-administration-ucr-command-line-set:

Set a UCR variable
~~~~~~~~~~~~~~~~~~

.. option:: set

   Use the :option:`set` sub-command to set a variable.
   Use only letters, periods, digits, hyphens, and forward slashes in variable names.
   See :numref:`ucr-set-example`.

   .. code-block:: console
      :caption: Set a UCR variable with :option:`set`
      :name: ucr-set-example

      $ univention-config-registry set VARIABLENAME=VALUE

   If the variable already exists,
   UCR updates its value.
   Otherwise, UCR creates the variable.

   When you set a new value for a UCR variable,
   UCR checks whether the value is compatible with the variable type.
   If the value is incompatible,
   UCR rejects the value and displays an error message.

   To verify the new value,
   use :option:`ucr get` as shown in :numref:`ucr-get-verify-example`.

   .. code-block:: console
      :caption: Verify a UCR variable value with :option:`ucr get`
      :name: ucr-get-verify-example

      $ univention-config-registry get VARIABLENAME

   .. caution::

      If you use ``--ignore-check``, UCR skips type checking.
      This might disrupt service configuration or corrupt data.
      Use this option only if you understand the risks.

When a variable changes,
UCR rewrites all linked configuration files
and displays the paths of the updated files in the console.
UCR doesn't restart the affected services automatically.
You need to restart the services that use the updated configuration files.

You can also change several variables in a single command,
as shown in :numref:`ucr-set-multiple-example`.
If these variables share a configuration file,
UCR rewrites it only once.

.. code-block:: console
   :caption: Set multiple UCR variables in a single command
   :name: ucr-set-multiple-example

   $ univention-config-registry set \
     dns/forwarder1=192.0.2.2 \
     sshd/xforwarding="no" \
     sshd/port=2222

UCR lets you assign a variable value conditionally.
To set a variable only when it doesn't already exist,
use a question mark (``?``) instead of an equals sign (``=``),
as shown in :numref:`ucr-set-conditional-example`.

.. code-block:: console
   :caption: Set a UCR variable conditionally
   :name: ucr-set-conditional-example

   $ univention-config-registry set dns/forwarder1?192.0.2.2

.. _system-administration-ucr-command-line-search:

Search for variables
~~~~~~~~~~~~~~~~~~~~

.. option:: search

   Use the :option:`search` sub-command to find a variable.
   :numref:`ucr-search-name-example` shows a search for variable names
   that contain ``ldap`` and their current values.
   The :option:`search` sub-command supports regular expressions.
   For the full syntax, see
   :external+python-docs:py:mod:`re — Regular expression operations <re>`
   in :cite:t:`python-docs`.

   .. code-block:: console
      :caption: Search for UCR variables by name
      :name: ucr-search-name-example

      $ univention-config-registry search ldap

   To search by value,
   see :numref:`ucr-search-value-example`,
   which lists all variables set to ``primary.example.com``.

   .. code-block:: console
      :caption: Search for UCR variables by value
      :name: ucr-search-value-example

      $ univention-config-registry search --value primary.example.com

.. _system-administration-ucr-command-line-delete:

Delete a UCR variable
~~~~~~~~~~~~~~~~~~~~~

.. option:: unset

   Use the :option:`unset` sub-command to delete a variable.
   :numref:`ucr-unset-example` shows an example that deletes the variable :envvar:`dns/forwarder2`.
   You can also delete multiple variables in one command.

   .. code-block:: console
      :caption: Delete a UCR variable with :option:`unset`
      :name: ucr-unset-example

      $ univention-config-registry unset dns/forwarder2

.. _system-administration-ucr-command-line-regenerate:

Regenerate a configuration file from its template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: commit

   Use the :option:`commit` sub-command to regenerate a configuration file from its template.
   :numref:`ucr-commit-example` shows an example that regenerates :file:`/etc/samba/smb.conf`.
   Use the :option:`commit` sub-command when you edit a template file manually,
   rather than when you change a UCR variable value.

   If you run :command:`ucr commit` without a filename,
   UCR rebuilds all managed files from their templates.
   This command is useful after restoring a backup
   or when troubleshooting template-related issues.

   .. code-block:: console
      :caption: Regenerate a configuration file with :option:`commit`
      :name: ucr-commit-example

      $ univention-config-registry commit /etc/samba/smb.conf

   To verify that UCR regenerated the file,
   inspect its content or check its modification time,
   as shown in :numref:`ucr-commit-verify-example`.

   .. code-block:: console
      :caption: Verify a regenerated configuration file with :option:`commit`
      :name: ucr-commit-verify-example

      $ stat /etc/samba/smb.conf

.. _system-administration-ucr-command-line-source:

Use UCR variables in shell scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: shell

   Use the :option:`shell` sub-command to display UCR variables
   and their current values in shell script format,
   as shown in :numref:`ucr-shell-example`.

   .. code-block:: console
      :caption: Display UCR variables in shell format
      :name: ucr-shell-example

      $ univention-config-registry shell ldap/server/name

UCR applies the following two conversions to the output:

* Forward slashes in variable names become underscores.

* UCR escapes characters with special meaning in shell,
  such as spaces, quotes, and dollar signs,
  to prevent unintended interpretation by the shell.

To use UCR variables as environment variables in a shell script,
pipe the output to :command:`eval`.
See :numref:`ucr-shell-eval-example` for an example.

.. code-block:: console
   :caption: Load UCR variables into a shell script with ``eval``
   :name: ucr-shell-eval-example

   $ eval "$(univention-config-registry shell ldap/server/name)"
   $ echo "$ldap_server_name"
   primary.example.com

.. _system-administration-ucr-precedence:

UCR variable precedence
-----------------------

UCR applies variable values in this priority order,
from lowest to highest:

Local variables
   Variables you set directly on the system with :option:`ucr set`.

Policy variables
   Variables distributed from the directory service that override local variables.
   If a higher-priority policy already overrides the variable you set,
   UCR displays a warning.

Schedule-level variables
   Variables that are valid only for a specified period.
   Set them with ``--schedule``.
   Nubus for UCS uses the schedule level for time-based automation.

Force-level variables
   Variables with the highest priority.
   They override policy and schedule variables.
   Set them with ``--force``.
   See :numref:`ucr-force-example` for an example.

   .. code-block:: console
      :caption: Override policy variables with ``--force``
      :name: ucr-force-example

      $ univention-config-registry set --force mail/messagesizelimit=1000000

.. _system-administration-ucr-templates:

Modify UCR templates
--------------------

A UCR template is a configuration file with markers.
UCR replaces these markers with variable values when it generates the file.

You can embed inline Python code in UCR templates.
Use it to add conditions or compute values from other variables.

UCR stores templates in :file:`/etc/univention/templates/files/`
and uses the absolute path of the configuration file as the template filename.
For example,
the template for :file:`/etc/issue` is at :file:`/etc/univention/templates/files/etc/issue`.

UCR template files must use Unix line endings: LF only, not CRLF.

.. caution::

   If you edit a template file on Windows,
   the editor may insert CRLF line endings
   that disrupt UCR processing.
   Before you edit the template,
   run :command:`dos2unix` ``FILENAME``
   to convert it to Unix format.

Nubus for UCS packages ship with UCR templates.
When you update a package,
UCR checks whether you modified the templates.
If you modified a template,
UCR preserves your changes.
It saves the updated package template
with the suffix :file:`.dpkg-new` or :file:`.dpkg-dist`
in the same directory
and logs a message to :file:`/var/log/univention/actualise.log`.

.. _system-administration-ucr-templates-reference:

Reference UCR variables in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To reference a UCR variable in a template, use the ``@%@`` marker.
:numref:`ucr-template-reference-example` shows the X11 forwarding option
in :file:`/etc/ssh/sshd_config`.

.. code-block::
   :caption: Reference a UCR variable in a template
   :name: ucr-template-reference-example

   X11Forwarding @%@sshd/xforwarding@%@

UCR detects variable references in templates
that use the ``@%@`` marker.
If your template uses inline Python code,
you must register additional variables explicitly.
For details, see :ref:`system-administration-ucr-templates-python`.

.. _system-administration-ucr-templates-python:

Integrate inline Python code in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can embed Python code blocks delimited by ``@!@``
to add conditions or compute values from other variables.
:numref:`ucr-python-ssl-example` shows how inline Python code in a template
configures SSL settings from UCR variables.

.. code-block::
   :caption: Configure SSL settings with inline Python code
   :name: ucr-python-ssl-example

   @!@
   if configRegistry.get('apache2/ssl/certificate'):
       print('SSLCertificateFile %s' %
           configRegistry['apache2/ssl/certificate'])
   @!@

UCR inserts the output of ``print`` statements
into the generated configuration file.
:numref:`ucr-python-configregistry-example` shows how to access UCR data
through the ``ConfigRegistry`` object.

For details about how UCR registers variables,
see :ref:`system-administration-ucr-templates-reference`.

.. code-block::
   :caption: Access UCR data through the ``ConfigRegistry`` object
   :name: ucr-python-configregistry-example

   @!@
   if configRegistry.get('version/version') and \
           configRegistry.get('version/patchlevel'):
       print('UCS %(version/version)s-%(version/patchlevel)s' %
           configRegistry)
   @!@

.. _system-administration-ucr-templates-info:

Register UCR variables in an info file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To register UCR variables in an info file:

#. Create an info file under :file:`/etc/univention/templates/info/`.
   Name the file after the package,
   for example :file:`{PACKAGENAME}.info`.

#. In the info file,
   list the UCR variables that your template uses.
   For the info file format,
   see :external+uv-dev-ref:ref:`ucr-info` in :cite:t:`developer-reference`.

#. If you add Python code that uses additional variables,
   either add them to the existing :file:`.info` file
   or create a new one for that package.

#. Run :command:`ucr update` to apply the changes.

.. _system-administration-ucr-policy:

Configure UCR variables with policies
-------------------------------------

Some UCR settings apply to a single system,
such as the hostname.
Other UCR settings apply to all systems in the domain,
such as the mail relay host setting.
Use the *UCR policy* in the *Policies* management module
to group variables and assign them to multiple computers.

.. _system-administration-ucr-policy-figure:

.. figure:: /images/computers_policy_apache_settings.*
   :alt: Policy-based configuration of the Apache start page and forced HTTPS

   Policy-based configuration of the Apache start page and forced HTTPS

To create and assign a UCR policy:

#. Open *Policies* management module
   in the *Management UI*.

#. Click :guilabel:`Add` and select :guilabel:`Univention Configuration Registry`.

#. Enter a :guilabel:`Name` for the policy.

#. Add at least one variable name in the :guilabel:`Variable` field
   and enter a value in the :guilabel:`Value` field.
   For an example, see :numref:`system-administration-ucr-policy-figure`.

#. Click :guilabel:`Create Policy` to create the policy.

#. Assign the policy to a computer object, container,
   or organizational unit (OU).
   For details, see :external+uv-nubus-manual:ref:`nubus-domain-policies-assign`.

UCR policies don't write values directly to the system.
Instead, Nubus for UCS writes the values to the LDAP object of the computer.
The computer reads the values during the next synchronization.
The :envvar:`ldap/policy/cron` UCR variable controls the synchronization interval.
The default interval is one hour.

To verify that UCR applied the policy after the next synchronization,
run :option:`ucr dump` on the target system.
For an example, see :numref:`ucr-policy-verify-example`.
To learn how UCR prioritizes variables,
see :ref:`system-administration-ucr-precedence`.

.. code-block:: console
   :caption: Verify a policy-applied UCR variable with :option:`ucr dump`
   :name: ucr-policy-verify-example

   $ univention-config-registry dump | grep VARIABLENAME

.. seealso::

   :external+uv-nubus-manual:ref:`nubus-domain-policies`
      in :cite:t:`uv-nubus-manual`
      for reference information about the *Policies* management module

   :external+uv-nubus-manual:ref:`nubus-domain-policies-assign`
      in :cite:t:`uv-nubus-manual`
      for information about how to assign policies.
