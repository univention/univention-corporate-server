.. _computers-administration-of-local-system-configuration-with-univention-configuration-registry:

Administration of local system configuration with Univention Configuration Registry
===================================================================================

|UCSUCR| is the central tool for managing the local system configuration of a
UCS-based system. Direct editing of the configuration files is usually not
necessary.

Settings are specified in a consistent format in a registry mechanism, the
so-called *Univention Configuration Registry variables*. These variables are
used to generate the configuration files used effectively by the
services/programs from the configuration templates (the so-called *Univention
Configuration Registry templates*).

This procedure offers a range of advantages:

* It is not usually necessary to edit any configuration files manually. This
  avoids errors arising from invalid syntax of configuration settings or
  similar.

* There is a uniform interface for editing the settings and the different
  syntax formats of the configuration files are hidden from the administrator.

* Settings are decoupled from the actual configuration file, i.e., if a
  software uses a different configuration format in a new version, a new
  template in a new format is simply delivered instead of performing
  time-consuming and error-prone conversion of the file.

* The variables used in a configuration file administrated with |UCSUCR| are
  registered internally. This ensures that when a UCR variable is changed, all
  the configuration files containing the changed variable are recreated.

|UCSUCR| variables can be configured in the command line using the
:command:`univention-config-registry` command (short form: :command:`ucr`) or via
the UMC module :guilabel:`Univention Configuration Registry`.

As the majority of packages perform their configuration via |UCSUCR| and the
corresponding basic settings need to be set up during the installation, hundreds
of |UCSUCR| variables are already set after the installation of a UCS system.

UCR variables can also be used efficiently in shell scripts for accessing
current system settings.

The variables are named according to a tree structure with a forward slash being
used to separate components of the name. For example, |UCSUCR| variables
beginning with ``ldap`` are settings which apply to the local directory service.

A description is given for the majority of variables explaining their use.

If a configuration file is administrated by a UCR template and the required
setting has not already been covered by an existing variable, the UCR template
should be edited instead of the configuration file. If the configuration were
directly adapted, the next time the file is regenerated - e.g., when a
registered UCR variable is set - the local modification will be overwritten
again. Adaptation of UCR templates is described in :ref:`ucr-templates-extend`.

Part of the settings configured in |UCSUCR| are system-specific (e.g., the
computer name); many settings can, however, be used on more then one computer.
The |UCSUCR| policy in the domain administration UMC modules can be used to
compile variables and apply them on more than one computer.

The evaluation of the |UCSUCR| variables on a UCS system comprises four stages:

* First the local |UCSUCR| variables are evaluated.

* The local variables are overruled by policy variables which are usually
  sourced from the directory service

* The ``--schedule`` option is used to set local variables which are only
  intended to apply for a certain period of time. This level of the |UCSUCR| is
  reserved for local settings which are automated by time-controlled mechanisms
  in |UCSUCS|.

* When the ``--force`` option is used in setting a local variable, settings
  adopted from the directory service and variables from the schedule level are
  overruled and the given value for the local system fixed instead. An example:

  .. code-block:: console

     $ univention-config-registry set --force mail/messagesizelimit=1000000

If a variable is set which is overwritten by a superordinate policy, a warning
message is given.

The use of the |UCSUCR| policy is documented in the :ref:`ucr-templates-policy`.

.. _computers-using-the-univention-management-console-web-interface:

Using the |UCSUMC| module
-------------------------

The UMC module :guilabel:`Univention Configuration Registry` can be used to
display and adjust the variables of a system. There is also the possibility of
setting new variables using :guilabel:`Add new variable`.

A search mask is displayed on the start page. All variables are classified using
a *Category*, for example all LDAP-specific settings.

The *Search attribute* can be entered as a filter in the search mask, which can
refer to the variable name, value or description.

Following a successful search, the variables found are displayed in a table with
the variable name and the value. A detailed description of the variable is
displayed when moving the mouse cursor over the variable name.

A variable can be edited by clicking on its name. A variable can be deleted by
right-clicking and selecting :guilabel:`Delete`.

.. _computers-using-the-command-line-front-end:

Using the command line front end
--------------------------------

.. program:: ucr

The command line interface of |UCSUCR| is run using the
:command:`univention-config-registry` command. Alternatively, the short form
:command:`ucr` can be used.

.. _computers-querying-a-ucr-variable:

Querying a UCR variable
~~~~~~~~~~~~~~~~~~~~~~~

.. option:: get

   A single |UCSUCR| variable can be queried with the parameter
   :option:`get`:

   .. code-block:: console

      $ univention-config-registry get ldap/server/ip


.. option:: dump

   The parameter :option:`dump` can also be used to display all currently set
   variables:

   .. code-block:: console

      $ univention-config-registry dump


.. _computers-setting-ucr-variables:

Setting UCR variables
~~~~~~~~~~~~~~~~~~~~~

.. option:: set

   The parameter :option:`set` is used to set a variable. The variable can be given
   any name consisting exclusively of letters, full stops, figures, hyphens and
   forward slashes.

   .. code-block:: console

      $ univention-config-registry set VARIABLENAME=VALUE


If the variable already exists, the content is updated; otherwise, a new entry
is created.

The syntax is not checked when a |UCSUCR| variable is set. The change to a
variable results in all configuration files for which the variable is registered
being rewritten immediately. The files in question are output on the console.

In doing so it must be noted that although the configuration of a service is
updated, the service in question is not restarted automatically! The restart
must be performed manually.

It is also possible to perform simultaneous changes to several variables in one
command line. If these refer to the same configuration file, the file is only
rewritten once.

.. code-block:: console

   $ univention-config-registry set \
   > dns/forwarder1=192.0.2.2 \
   > sshd/xforwarding="no" \
   > sshd/port=2222

A conditional setting is also possible. For example, if a value should only be
saved in a |UCSUCR| variable when the variable does not yet exist, this can be
done by entering a question mark (``?``) instead of the equals sign ( ``=``)
when assigning values.

.. code-block:: console

   $ univention-config-registry set dns/forwarder1?192.0.2.2


.. _computers-searching-for-variables-and-set-values:

Searching for variables and set values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: search

   The parameter :option:`search` can be used to search for a variable. This
   command searches for variable names which contain ``nscd`` and displays these
   with their current assignments:

   .. code-block:: console

      $ univention-config-registry search nscd


   Alternatively, searches can also be performed for set variable values. This
   request searches for all variables set to ``primary.example.com``:

   .. code-block:: console

      $ univention-config-registry search --value primary.example.com


Search templates in the form of regular expressions can also be used in
the search. The complete format is documented at
https://docs.python.org/2/library/re.html.

.. _computers-deleting-ucr-variables:

Deleting UCR variables
~~~~~~~~~~~~~~~~~~~~~~

.. option:: unset

   The parameter :option:`unset` is used to delete a variable. The following
   example deletes the variable :envvar:`dns/forwarder2`. It is also possible here
   to specify several variables to be deleted:

   .. code-block:: console

      $ univention-config-registry unset dns/forwarder2


.. _computers-regeneration-of-configuration-files-from-their-template:

Regeneration of configuration files from their template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: commit

   The parameter :option:`commit` is used to regenerate a configuration file
   from its template. The name of the configuration file is entered as a
   parameter, e.g.:

   .. code-block:: console

      $ univention-config-registry commit /etc/samba/smb.conf


As UCR templates are generally regenerated automatically when UCR variables are
edited, this is primarily used for tests.

If no filename is given when running :command:`ucr commit`, all of the files
managed by |UCSUCR| will be regenerated from the templates. It is, however, not
generally necessary to regenerate all the configuration files.

.. _computers-sourcing-variables-in-shell-scripts:

Sourcing variables in shell scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. option:: shell

   The parameter :option:`shell` is used to display |UCSUCR| variables and their
   current assignments in a format that can be used in shell scripts.

   .. code-block:: console

      $ univention-config-registry shell ldap/server/name


Different conversions are involved in this: forward slashes in variable names
are replaced with underscores and characters in the values which have a
particular significance in shell scripts are included in quotation marks to
ensure they are not altered.

The |UCSUCR| output must be executed via the command :command:`eval` for
|UCSUCR| variables to be able to be read in a shell script as environment
variables:

.. code-block:: console

   # eval "$(univention-config-registry shell ldap/server/name)"
   # echo "$ldap_server_name"
   primary.firma.de


.. _ucr-templates-policy:

Policy-based configuration of UCR variables
-------------------------------------------

Part of the settings configured in |UCSUCR| are system-specific (e.g., the
computer name); many settings can, however, be used on more then one computer.
The *Univention Configuration Registry* policy managed in the UMC module
:guilabel:`Policies` can be used to compile variables and apply them on more
than one computer.

.. _policy-apache-settings:

.. figure:: /images/computers_policy_apache_settings.*
   :alt: Policy-based configuration of the Apache start page and forced HTTPS

   Policy-based configuration of the Apache start page and forced HTTPS

Firstly, a *Name* must be set for the policy which is to be created, under which
the variables will later be assigned to the individual computer objects.

In addition, at least one *Variable* must be configured and a *Value* assigned.

This policy can then be assigned to a computer object or a container or OU
(see :ref:`central-policies-assign`). Note that the evaluation of
configured values differs from other policies: The values are not
forwarded directly to the computer, but rather written on the assigned
computer by Univention Directory Policy. The time interval used for this
is configured by the |UCSUCRV| :envvar:`ldap/policy/cron` and is
set to hourly as standard.

.. _ucr-templates-extend:

Modifying UCR templates
-----------------------

In the simplest case, a |UCSUCR| template is a copy of the original
configuration file in which the points at which the value of a variable
are to be used contain a reference to the variable name.

Inline Python code can also be integrated for more complicated
scenarios, which then also allows more complicated constructions such as
conditional assignments.

.. note::

   |UCSUCR| templates are included in the corresponding software packages
   as configuration files. When packages are updated, a check is
   performed for whether any changes have been made to the configuration
   files.

   If configuration files are no longer there in the form in which they were
   delivered, they will not be overwritten. Instead a new version will be
   created in the same directory with the ending :file:`.debian.dpkg-new`.

   If changes are to be made on the |UCSUCR| templates, these templates are also
   not overwritten during the update and are instead re-saved in the same
   directory with the ending :file:`.dpkg-new` or :file:`.dpkg-dist`.
   Corresponding notes are written in the
   :file:`/var/log/univention/actualise.log` log file. This only occurs if UCR
   templates have been locally modified.

The UCR templates are stored in the :file:`/etc/univention/templates/files/`
directory. The path to the templates is the absolute path to the configuration
file with the prefixed path to the template directory. For example, the template
for the :file:`/etc/issue` configuration file can be found under
:file:`/etc/univention/templates/files/etc/issue`.

For the configuration files to be processed correctly by |UCSUCR| they must be
in UNIX format. If configuration files are edited in DOS or Windows, for
example, control characters are inserted to indicate line breaks, which can
disrupt the way |UCSUCR| uses the file.

.. _ucr-templates-extend-simple:

Referencing of UCR variables in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the simplest case, a UCR variable can be directly referenced in the template.
The variable name framed by the string ``@%@`` represents the wildcard. As an
example the option for the activation of X11 forwarding in the configuration
file :file:`/etc/ssh/sshd_config` of the OpenSSH server:

.. code-block::

   X11Forwarding @%@sshd/xforwarding@%@

Newly added references to UCR variables are automatically evaluated by
templates; additional registration is only required with the use of inline
Python code (see :ref:`ucr-templates-extend-python`).

.. _ucr-templates-extend-python:

Integration of inline Python code in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any type of Python code can be embedded in UCR templates by entering a code
block framed by the string ``@!@``. For example, these blocks can be used to
realize conditional requests so that when a parameter is changed via a variable,
further dependent settings are automatically adopted in the configuration file.
The following code sequence configures for example network settings using the
|UCSUCR| settings:

.. code-block::

   @!@
   if configRegistry.get('apache2/ssl/certificate'):
       print('SSLCertificateFile %s' %
           configRegistry['apache2/ssl/certificate'])
   @!@


All the data output with the print function are written in the generated
configuration file. The data saved in |UCSUCR| can be requested via the
``ConfigRegistry`` object, e.g.:

.. code-block::

   @!@
   if configRegistry.get('version/version') and \
           configRegistry.get('version/patchlevel'):
       print('UCS %(version/version)s-%(version/patchlevel)s' %
           configRegistry)
   @!@


In contrast to directly referenced UCR variables (see
:ref:`ucr-templates-extend-simple`), variables accessed in inline Python code
must be explicitly registered.

The |UCSUCR| variables used in the configuration files are registered in *info*
files in the :file:`/etc/univention/templates/info/` directory which are usually
named after the package name with the file ending :file:`.info`. If new Python
code is entered into the templates or the existing code changed in such a way
that it requires additional or different variables, one of the existing
:file:`.info` files will need to be modified or a new one added.

Following the changing of :file:`.info` files, the :command:`ucr update` command
must be run.

