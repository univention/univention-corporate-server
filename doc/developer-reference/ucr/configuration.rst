.. _ucr-conf:

Configuration files
===================

Packages can use the UCR functionality to create customized configuration files
themselves. UCR diverts files shipped by Debian packages and replaces them by
generated files. If variables are changed, the affected files are committed,
which regenerated their content. This diversion is persistent and even outlives
updates, so they are not overwritten by configuration files of new packages.

For this, packages need to ship additional files:

:samp:`conffiles/{path/to/file}`
   This template file is used to create the target file. There exist two
   variants:

   #. A *single file template* consists of only a single file, from which the
      target file is created.

   #. A *multi file template* can consist of multiple file fragments, which are
      concatenated to form the target file.

   For more information, see :ref:`ucr-conffiles`.

:samp:`debian/{package}.univention-config-registry`
   This mandatory information file describes the each template file. It
   specifies the type of the template and lists the UCR variable names, which
   shall trigger the regeneration of the target file.

   For more information, see :ref:`ucr-info`.

:samp:`debian/{package}.univention-config-registry-variables`
   This optional file can add descriptions to UCR variables, which should
   describe the use of the variable, its default and allowed values.

   For more information, see :ref:`ucr-variables`.

:samp:`debian/{package}.univention-config-registry-categories`
   This optional file can add additional categories to group UCR variables.

   For more information, see :ref:`ucr-categories`.

:samp:`debian/{package}.univention-service`
   This optional file is used to define long running services.

   For more information, see :ref:`ucr-categories`.

In addition to these files, code needs to be inserted into the package maintainer
scripts (see :ref:`deb-scripts`), which registers and unregisters these files.
This is done by calling :command:`univention-install-config-registry` from
:file:`debian/rules` during the package build ``binary`` phase. The command is
part of the :program:`univention-config-dev` package, which needs to be added as
a ``Build-Depends`` build dependency of the source package in
:file:`debian/control`.

.. _ucr-info:

:samp:`debian/{package}.univention-config-registry`
---------------------------------------------------

.. index::
   single: config registry
   single: configuration files

This file describes all template files in the package. The file is processed and
copied by :command:`univention-install-config-registry` into
:file:`/etc/univention/templates/info/` when the package is built.

It can consist of multiple sections, where sections are separated by one blank
line. Each section consists of multiple key-value-pairs separated by a colon
followed by one blank. A typical entry has the following structure:

.. code-block::

   Type: <type>
   [Multifile|File]: <filename>>
   [Subfile: <fragment-filename>]
   Variables: <variable1>
   ...

``Type`` specifies the type of the template, which the following sections
describe in more detail.

.. _ucr-file:

``File``
~~~~~~~~

.. index::
   pair: config registry; template
   pair: template; single file

A single file template is specified as type ``file``. It defines a template,
were the target file is created from only a single source file. A typical entry
hat the following structure:

.. code-block::

   Type: file
   File: <filename>
   Variables: <variable1>
   User: <owner>
   Group: <group>
   Mode: <file-mode>
   Preinst: <module>
   Postinst: <module>
   ...

The following keys can be used:

``File`` (required)
   Specifies both the target and source file name, which are identical. The
   source file containing the template must be put below the :file:`conffiles/`
   directory. The file can contain any textual content and is processed as
   described in :ref:`ucr-conffiles`.

   The template file is installed to :file:`/etc/univention/templates/files/`.

``Variables`` (optional)
   This key can be given multiple times and specifies the name of UCR variables,
   which trigger the file commit process. This is normally only required for
   templates using ``@!@`` Python code regions. Variables used in ``@%@``
   sections do not need to be listed explicitly, since :command:`ucr` extracts
   them automatically.

   The variable name is actually a Python regular expression, which can be used
   to match, for example, all variable names starting with a common prefix.

``User`` (optional); ``Group`` (optional); ``Mode`` (optional)
   These specify the symbolic name of the user, group and octal file permissions
   for the created target file. If no values are explicitly provided, then
   ``root:root`` is used by default and the file mode is inherited from the
   source template.

``Preinst`` (optional); ``Postinst`` (optional)
   These specify the name of a Python module located in
   :file:`/etc/univention/templates/modules/`, which is called before and after
   the target file is re-created. The module must implement the following two
   functions:

   .. code-block:: python

      def preinst(
          config_registry: ConfigRegistry,
          changes: Dict[str, Tuple[Optional[str], Optional[str]]],
      ) -> None:
          pass
      def postinst(
          config_registry: ConfigRegistry,
          changes: Dict[str, Tuple[Optional[str], Optional[str]]],
      ) -> None:
          pass

   Each function receives two arguments: The first argument ``config_registry``
   is a reference to an instance of ``ConfigRegistry``. The second argument
   ``changes`` is a dictionary of 2-tuples, which maps the names of all changed
   variables to (``old-value``, ``new-value``).

   :command:`univention-install-config-registry` installs the module file to
   :file:`/etc/univention/templates/modules/`.

If a script :samp:`/etc/univention/templates/scripts/{full-path-to-file}`
exists, it will be called after the file is committed. The script is called with
the argument ``postinst``. It receives the same list of changed variables as
documented in :ref:`ucr-script`.

.. _ucr-multifile:

``Multifile``
~~~~~~~~~~~~~

.. index::
   pair: config registry; template
   pair: template; multi file

A multi file template is specified once as type ``multifile``, which describes
the target file name. In addition to that multiple sections of type ``subfile``
are used to describe source file fragments, which are concatenated to form the
final target file. A typical multifile has the following structure:

.. code-block::

   Type: multifile
   Multifile: <target-filename>
   User: <owner>
   Group: <group>
   Mode: <file-mode>
   Preinst: <module>
   Postinst: <module>
   Variables: <variable1>

   Type: subfile
   Multifile: <target-filename>
   Subfile: <fragment-filename>
   Variables: <variable1>
   ...

The following keys can be used:

``Multifile`` (required)
   This specifies the target file name. It is also used to link the
   ``multifile`` entry to its corresponding ``subfile`` entries.

``Subfile`` (required)
   The source file containing the template fragment must be put below the
   :file:`conffiles/` directory in the Debian source package. The file can
   contain any textual content and is processed as described in
   :ref:`ucr-conffiles`. The template file is installed to
   :file:`/etc/univention/templates/files/`.

   Common best practice is to start the filename with two digits to allow
   consistent sorting and to put the file in the directory named like the target
   filename suffixed by ``.d``, that is
   :samp:`conffiles/{target-filename}.d/{00fragment-filename}`.

``Variables`` (optional)
   Variables can be declared in both the ``multifile`` and ``subfile`` sections.
   The variables from all sections trigger the commit of the target file. Until
   UCS-2.4 only the ``multifile`` section was used, since UCS-3.0 the
   ``subfile`` section should be preferred (if needed).

``User`` (optional); ``Group`` (optional); ``Mode`` (optional); ``Preinst`` (optional); ``Postinst`` (optional)
   Same as above for ``file``.

The same script hook as above for ``file`` is also supported.

.. _ucr-script:

``Script``
~~~~~~~~~~

.. index::
   pair: config registry; template
   pair: template; script

A script template allows an external program to be called when specific UCR
variables are changed. A typical script entry has the following structure:

.. code-block::

   Type: script
   Script: <filename>
   Variables: <variable1>

The following keys can be used:

``Script`` (required)
   Specifies the filename of an executable, which is installed to
   :file:`/etc/univention/templates/scripts/`.

   The script is called with the argument ``generate``. It receives the list of
   changed variables on standard input. For each changed variable a line
   containing the name of the variable, the old value, and the new value
   separated by ``@%@`` is sent.

``Variables`` (required)
   Specifies the UCR variable names, which should trigger the script.

.. warning::

   There is **no** guarantee that ``Script`` is executed **after** a file has
   been committed. If this is required for example for restarting a service
   place the script instead at the location mentioned at the end of
   :ref:`ucr-file`.

.. note::

   The script interface is quiet limited for historical reasons. Consider it
   deprecated in favor of :ref:`ucr-module`.

.. _ucr-module:

``Module``
~~~~~~~~~~

.. index::
   pair: config registry; template
   pair: template; module

A module template allows a Python module to be run when specific UCR variables
are changed. A typical module entry has the following structure:

.. code-block::

   Type: module
   Module: <filename>
   Variables: <variable1>


The following keys can be used:

``Module`` (required)
   Specifies the filename of a Python module, which is installed to
   :file:`/etc/univention/templates/modules/`.

   The module must implement the following function:

   .. code-block:: python

      def handler(
          config_registry: ConfigRegistry,
          changes: Dict[str, Tuple[Optional[str], Optional[str]]],
      ) -> None:
          pass

   The function receives two arguments: The first argument ``config_registry``
   is a reference to an instance of ``ConfigRegistry``. The second argument
   ``changes`` is a dictionary of 2-tuples, which maps the names of all changed
   variables to (``old-value``, ``new-value``).

   :command:`univention-install-config-registry` installs the module to
   :file:`/etc/univention/templates/modules/`.

``Variables`` (required)
   Specifies the UCR variable names, which should trigger the module.

.. warning::

   There is **no** guarantee that ``Module`` is executed **after** a file has
   been committed. If this is required for e.g. restarting a service use
   ``Preinst`` or ``Postinst`` as mentioned in :ref:`ucr-file` instead.

.. _ucr-variables:

:samp:`debian/{package}.univention-config-registry-variables`
-------------------------------------------------------------

.. index::
   single: config registry; descriptions

For UCR variables a description should be registered. This description is shown
in the *Univention Config Registry* module of the UMCas a mouse-over. It can
also be queried by running :samp:`ucr info {variable/name}` on the command line.

The description is provided on a per-package basis as a file, which uses the
ini-style format. The file is processed and copied by
:command:`univention-install-config-registry-info` into
:file:`/etc/univention/registry.info/variables/`. The command
:command:`univention-install-config-registry-info` is invoked indirectly by
:command:`univention-install-config-registry`, which should be called instead
from :file:`debian/rules`.

For each variable a section of the following structure is defined:

::

   [<variable/name>]
   Description[en]=<description>
   Description[<language>]=<description>
   Type=<type>
   Default=<default value>
   ReadOnly=<yes|no>
   Categories=<category,...>

``[``\ :samp:`{variable/name}`\ ``]`` (required)
   For each variable description one section needs to be created. The name of
   the section must match the variable name.

   To describe multiple variables with a common prefix and/or suffix, the
   regular expression ``.*`` can be used to match any sequence of characters.
   This is the only supported regular expression!

``Description[``\ :samp:`{language}`\ ``]`` (required)
   A descriptive text for the variable. It should mention the valid and default
   values. The description can be given in multiple languages, using the
   two-letter-code following :cite:t:`ISO639`.

``Type`` (required)
   The syntax type for the value. This is unused in UCS-3.1, but future versions
   might use this for validating the input. Valid values include ``str`` for
   strings, ``bool`` for boolean values, and ``int`` for integers.

``Default`` (optional)
   .. versionadded:: 5.0-0

   The default value of the UCR variable which is applied if the variable is not
   set. The default value might be a UCR pattern referencing other variables,
   for example ``Default=@%@another/variable@%@ example``.


``ReadOnly`` (optional)
   This declares a variable as read-only and prohibits changing the value
   through UMC. The restriction **isn't** applied when using the command line
   tool :command:`ucr`. Valid values are ``true`` for read-only and ``false``,
   which is the default.

``Categories`` (required)
   A list of categories, separated by comma. This is used to group related UCR
   variables. New categories don't need to be declared explicitly, but it is
   recommended to do so following :ref:`ucr-categories`.

.. _ucr-categories:

:samp:`debian/{package}.univention-config-registry-categories`
--------------------------------------------------------------

.. index::
   single: config registry; categories

UCR variables can be grouped into categories, which can help administrators to
find related settings. Categories are referenced from
:file:`.univention-config-registry-variables` files (see :ref:`ucr-variables`).
They are created on-the-fly, but can be described further by explicitly defining
them in a :file:`.univention-config-registry-categories` file.

The description is provided on a per-package basis as a file, which uses the
INI-style format. The file is processed and copied by
:command:`univention-install-config-registry-info` into
:file:`/etc/univention/registry.info/categories/`. The command
:command:`univention-install-config-registry-info` is invoked indirectly by
:command:`univention-install-config-registry`, which should be called instead
from :file:`debian/rules`.

For each category a section of the following structure is defined:

.. code-block::

   [<category-name>]
   name[en]=<name>
   name[<language>]=<translated-name>
   icon=<file-name>

``[``\ :samp:`{category-name}`\ ``]``
   For each category description one section needs to be created.

``name[``\ :samp:`{language}`\ ``]`` (required)
   A descriptive text for the category. The description can be given in
   multiple languages, using the two-letter-code following :cite:t:`ISO639`.

``icon`` (required)
   The filename of an icon in either the Portable Network Graphics
   (PNG) format or Graphics Interchange Format (GIF). This is unused in
   UCS-3.1, but future versions might display this icon for variables in
   this category.

.. _ucr-services:

:samp:`debian/{package}.univention-service`
-------------------------------------------

.. index::
   single: config registry; services

Long running services should be registered with UCR and UMC. This enables
administrators to control these daemons using the UMC module *System services*.

The description is provided on a per-package basis as a file, which uses the
ini-style format. The file is processed and copied by
:command:`univention-install-service-info` into
:file:`/etc/univention/service.info/services/`. The command
:command:`univention-install-service-info` is invoked indirectly by
:command:`univention-install-config-registry`, which should be called instead
from :file:`debian/rules`.

For each service a section of the following structure is defined:

.. code-block::

   [<service-name>]
   description[<language>]=<description>
   start_type=<service-name>/autostart
   systemd=<service-name>.service
   icon=<service/icon_name>
   programs=<executable>
   name=<service-name>
   init_scipt=<init.name>

``[``\ :samp:`{service-name}`\ ``]``; ``name=``\ :samp:`{service-name}` (optional)
   For each daemon one section needs to be created. The service-name
   should match the name of the init-script in ``/etc/init.d/``. If the name differs, it
   can be overwritten by the ``name=`` property.

``description[``\ :samp:`{language}`\ ``]`` (required)
   A descriptive text for the service. The description can be given in multiple
   languages, using the two-letter-code following :cite:t:`ISO639`.

``start_type`` (required)
   Specifies the name of the UCR variable, which controls if the service should
   be started automatically. It is recommended to use the shell library
   :file:`/usr/share/univention-config-registry/init-autostart.lib` to evaluate
   the setting from the init-script of the service. If the variable is set to
   ``false`` or ``no``, the service should never be started. If the variable is
   set to ``manually``, the service is explicitly not started during system
   boot. The service can still be started manually. It should be noted that if
   other services are started that have a dependency on a service marked as
   ``manually``, the service marked as ``manually`` will also be started.

``systemd`` (optional)
   A comma separated list of :program:`systemd` service names, which are
   enabled/disabled/masked when ``start_type`` is used. This defaults to the
   name of the service plus the suffix ``.service``.

``init_script`` (optional)
   The name of the legacy init script below ``/etc/init.d/``. This defaults to
   the name of the service. This option should not be used any more in favor of
   :program:`systemd`.

``programs`` (required)
   A comma separated list of commands, which must be running to qualify the
   service as running. Each command name is checked against
   :file:`/proc/*/cmdline`. To check the processes for additional arguments, the
   command can also consist of additional shell-escaped arguments.

``icon`` (unused)
   This is unused in UCS, but future versions might display the icon for the
   service. The file name of an icon in either Portable Network Graphics (PNG)
   format or Graphics Interchange Format (GIF) format.
