.. _join-write:

Writing join scripts
====================

.. index::
   single: join script; writing

Similar to the Debian maintainer scripts (see :ref:`deb-scripts`) they should be
idempotent. They should transform the system from any state into the state
required by the package, that is:

* They should create newly introduced objects in the Univention directory
  service.

* They should not fail, if the object already exists.

* They should be careful about modifying objects, which might have been modified
  by the administrator in the past.

.. important::

   Join scripts may be called from multiple system roles and different versions.
   Therefore, it is important that these scripts **do not destroy or remove data
   still used by other systems!**

.. _join-minimal:

Basic join script example
-------------------------

This example provides a template for writing join scripts. The package
is called :program:`join-template` and just contains a join
and an unjoin script. They demonstrate some commonly used functions.

Source code:
:uv:src:`doc/developer-reference/join/join-template/`

:file:`50join-template.inst`
   The join script in UCS packages is typically located in the package
   root directory. It has the following base structure:

   .. code-block:: bash

      #!/bin/sh

      ## joinscript api: bindpwdfile

      VERSION=1
      . /usr/share/univention-join/joinscripthelper.lib
      joinscript_init

      SERVICE="MyService"

      eval "$(ucr shell)"

      . /usr/share/univention-lib/ldap.sh
      ucs_addServiceToLocalhost "$SERVICE" "$@"

      udm "computers/$server_role" modify "$@" \
          --dn "$ldap_hostdn" \
          --set reinstall=0 || die

      # create container for extended attributes to be placed in
      udm container/cn create "$@" \
          --ignore_exists \
          --position "cn=custom attributes,cn=univention,$ldap_base" \
          --set name="myservice" || die

      # some extended attributes would be added here

      joinscript_save_current_version
      exit 0


   Note the essential argument ``"$@"`` when :command:`udm` is invoked, which
   passes on the required LDAP credentials described in :ref:`join-secret`.

   .. versionadded:: 4.3

      Since :uv:erratum:`4.3x85`, credentials can also be passed through a file
      to prevent the password from being visible from the process tree.

   To enable this API one of the following comments must be placed inside the
   join script:

   ``## joinscript api: bindpwdfile``
      Credentials from :command:`univention-join` and
      :command:`univention-run-join-script` are always passed through the two
      parameters ``--binddn`` and ``--bindpwdfile``.

      .. deprecated:: 4.4

         The old parameter :samp:`--bindpwd {secret}` is no longer supported and
         used.

      .. versionchanged:: 5.0

         This is the default since UCS 5.

   ``## joinscript api: nocredentials``
      The credentials will be stored in three files named:

      * :file:`/var/run/univention-join/binddn`

      * :file:`/var/run/univention-join/bindpwd`

      * :file:`/var/run/univention-join/samba-authentication-file`

      They exist only while :command:`univention-join` or
      :command:`univention-run-join-script` are running. Each individual join
      script will be called with no extra options.

:file:`debian/control`
   The package uses two shell libraries, which are described in more
   detail in :ref:`join-libraries`. Both packages
   providing them must be added as additional runtime dependencies.

   The package needs to add :program:`univention-join-dev` as
   build dependency.

   .. code-block::

      Source: join-template
      Section: univention
      Priority: optional
      Maintainer: Univention GmbH <packages@univention.de>
      Build-Depends:
       debhelper-compat (= 12),
       univention-join-dev (>= 12),
      Standards-Version: 4.3.0.3

      Package: join-template
      Architecture: all
      Depends: univention-join (>= 5.0.20-1),
       shell-univention-lib (>= 2.0.17-1),
       ${misc:Depends}
      Description: An example package for join scripts
       This purpose of this package is to show how
       Univention Join scripts are used.
       .
       For more information about UCS, refer to:
       https://www.univention.de/


:file:`debian/rules`
   During package build time
   :command:`dh-univention-join-install` needs to be called.
   This should be done using the sequence
   ``univention-join`` in
   :file:`debian/rules`:

   .. code-block:: makefile

      #!/usr/bin/make -f
      %:
      	dh $@ --with univention-join

   This installs the scripts into the right directories. It also adds code
   fragments to the :file:`.debhelper` files to call them. Those calls are
   inserted into the Debian maintainer scripts at the location marked with
   ``#DEBHELPER#``. As many join scripts need to restart services, which depend
   on configuration files managed through |UCSUCR|, new |UCSUCRV| should be set
   *before* this section.

.. _join-exit-code:

Join script exit codes
----------------------

.. index::
   single: join script; exit codes
   single: join script; return codes

Join scripts must return the following exit codes:

``0``
   The join script was successful and completed all tasks to join the software
   package on the system into the domain. All required entries in the Univention
   directory service were created or do already exist as expected.

   The script will be marked as successfully run. As a consequence the join
   script will not be called again in this version.

``1``
   The script did not complete and some tasks to fully join the system into the
   domain are still pending. Some entries couldn't be created in LDAP or exist
   in a state, which is incompatible with this version of the package.

   The script needs to be run again after fixing the problem, either manually or
   automatically.

``2``
   Some internal functions were called incorrectly. For example the credentials
   were wrong.

   Run the join script again.

.. _join-libraries:

Join script libraries
---------------------

.. index::
   single: join script; library
   single: join script; helpers

The package :program:`univention-join` contains two shell libraries, which
provide functions which help in writing join scripts:

.. _join-libraries-join:

:file:`joinscripthelper.lib`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The package contains the shell library
:file:`/usr/share/univention-join/joinscripthelper.lib`.
It provides functions related to updating the join status file. It is
used by the join script itself.

.. glossary::

   joinscript_init
      This function parses the status file and exits the shell script, if a
      record is found with a version greater or equal to value of the
      environment variable :envvar:`VERSION`. The name of the join
      script is derived from :envvar:`$0`.

   joinscript_save_current_version
      This function appends a new record to the end of the status file
      using the version number stored in the environment variable
      :envvar:`VERSION`.

   joinscript_check_any_version_executed
      This function returns success (``0``), if any
      previous version of the join scripts was successfully executed.
      Otherwise it returns a failure (``1``).

   joinscript_check_specific_version_executed version
      This function returns success (``0``), if the
      specified version ``version`` of the join scripts was
      successfully executed. Otherwise it returns a failure
      (``1``).

   joinscript_check_version_in_range_executed min max
      This function returns success (``0``), if any
      successfully run version of the join script falls within the range
      ``min``..``max``, inclusively.
      Otherwise it returns a failure (``1``).

   joinscript_extern_init join-script
      The check commands mentioned above can also be used in other shell
      programs, which are not join scripts. There the name of the join
      script to be checked must be explicitly given. Instead of calling
      :command:`joinscript_init`, this function requires an
      additional argument specifying the name of the
      ``join-script``.

   joinscript_remove_script_from_status_file name
      Removes the given join script from the join script status file
      :file:`/var/univention-join/status`. The ``name`` should be the basename
      of the joinscript without the prefixed digits and the suffix
      :file:`.inst`. So if the joinscript
      :file:`/var/lib/univention-install/50join-template.inst` shall be removed,
      one has to run :samp:`joinscript_remove_script_from_status_file
      {join-template}`. Primarily used in unjoin scripts.

   die
      A convenience function to exit the join script with an error code.
      Used to guarantee that LDAP modifications were successful:
      :command:`some_udm_create_call \|\| die`

These functions use the following environment variables:

.. envvar:: VERSION

   This variable must be set before :command:`joinscript_init` is invoked. It
   specifies the version number of the join script and is used twice:

   #. It defines the current version of the join script.

   #. If that version is already recorded in the status file, the join script
      qualifies as having been run successfully and the re-execution is
      prevented. Otherwise the join status is incomplete and the script needs
      to be invoked again.

   The version number should be incremented for a new version of the package,
   when the join script needs to perform additional modifications in LDAP
   compared to any previous packaged version.

   The version number must be a positive integer. The variable assignment in the
   join script must be on its own line. It may optionally quote the version
   number with single quotes (``'``) or double quotes (``"``). The following
   assignment are valid:

   .. code-block:: console

      VERSION=1
      VERSION='2'
      VERSION="3"


.. envvar:: JS_LAST_EXECUTED_VERSION

   This variable is initialized by :command:`joinscript_init` with the latest
   version found in the join status file. If no version of the join script was
   ever executed and thus no record exists, the variable is set to ``0``. The
   join script can use this information to decide what to do on an upgrade.

.. _join-libraries-shell:

:program:`join.sh`
~~~~~~~~~~~~~~~~~~

The package contains the shell library
:file:`/usr/share/univention-lib/join.sh`. It is used by by Debian maintainer
scripts to register and call join scripts. Before UCS 5 the functions were part
of :file:`/usr/share/univention-lib/base.sh` provided by the package
:program:`shell-univention-lib`.

Since package version ``>= 2.0.17-1`` it provides the following functions:

:command:`call_joinscript` :samp:`[--binddn {bind-dn} [--bindpwdfile {filename}]] [{XXjoin-script.inst}]`
   This calls the join script called :file:`XXjoin-script.inst` from the
   directory :file:`/usr/lib/univention-install/`. The optional LDAP credentials
   ``bind-dn`` and ``filename`` are passed on as-is.

:command:`call_joinscript_on_dcmaster` :samp:`[--binddn {bind-dn} [--bindpwdfile {filename}]] [{XXjoin-script.inst}]`
   Similar to :command:`call_joinscript`, but also checks the system role and
   only executes the script on the |UCSPRIMARYDN|.

:command:`remove_joinscript_status` :samp:`[{name}]`
   Removes the given join script ``name`` from the join script status file
   :file:`/var/univention-join/status`. Note that this command does the same as
   :command:`joinscript_remove_script_from_status_file` provided by
   :program:`univention-join` (see :ref:`join-libraries-join`).

:command:`call_unjoinscript` :samp:`[--binddn {bind-dn} [--bindpwdfile {filename}]] [{XXunjoin-script.uinst}]`
   Calls the given unjoin script ``unjoin-script`` on |UCSPRIMARYDN| and
   |UCSBACKUPDN| systems. The filename must be relative to the directory
   :file:`/usr/lib/univention-install`. The optional LDAP credentials
   ``bind-dn`` and ``bind-password`` respective ``filename`` are passed on
   as-is. Afterwards the unjoin script is automatically deleted.

:command:`delete_unjoinscript` :samp:`[{XXunjoin-script.uinst}]`
   Deletes the given unjoin script ``XXunjoin-script.uinst``, if it does not
   belong to any package. The file name must be relative to the directory
   :file:`/usr/lib/univention-install`.

:command:`stop_udm_cli_server`
   When :command:`univention-directory-manager` is used the first time a server
   is started automatically that caches some information about the available
   modules. When changing some of this information, for example when adding or
   removing extended attributes, the server should be stopped manually.

:program:`ldap.sh`
~~~~~~~~~~~~~~~~~~

The package also contains the shell library
:file:`/usr/share/univention-lib/ldap.sh`. It provides convenience functions to
query the Univention directory service and modify objects. For (un)join scripts
the following functions might be important:

:command:`ucs_addServiceToLocalhost` :samp:`{servicename} [--binddn {bind-dn} [--bindpwdfile {filename}]]`
   Registers the additional service ``servicename`` in the LDAP object
   representing the local host. The optional LDAP credentials ``bind-dn`` and
   ``bind-password`` respective ``filename`` are passed on as-is.

   .. code-block:: bash
      :caption: Service registration in join script
      :name: join-add-service

      ucs_addServiceToLocalhost "MyService" "$@"

:command:`ucs_removeServiceFromLocalhost` :samp:`{servicename} [--binddn {bind-dn} [--bindpwdfile {filename}]]`
   Removes the service ``servicename`` from the LDAP object representing the
   local host, effectively reverting an :command:`ucs_addServiceToLocalhost`
   call. The optional LDAP credentials ``bind-dn`` and ``bind-password``
   respective ``filename`` are passed on as-is.

   .. code-block:: bash
      :caption: Service un-registration in unjoin script
      :name: join-remove-service

      ucs_removeServiceFromLocalhost "MyService" "$@"


:command:`ucs_isServiceUnused` :samp:`{servicename} [--binddn {bind-dn} [--bindpwdfile {filename}]]`
   Returns ``0``, if no LDAP host object exists where the service
   ``servicename`` is registered with.

   .. code-block:: bash
      :caption: Check for unused service in unjoin script
      :name: join-unused-service

      if ucs_isServiceUnused "MyService" "$@"
      then
          uninstall_my_service
      fi

.. _join-ucs-register-ldap-extension:

.. program:: ucs_registerLDAPExtension

:command:`ucs_registerLDAPExtension` :samp:`[--binddn {bind-dn} --bindpwdfile {filename}]` ``{{--schema`` :samp:`{filename}.schema | --acl {filename}.acl | --udm_syntax {filename}.py | --udm_hook {filename}.py` ``...}`` :samp:`| --udm_module {filename}.py [--messagecatalog {filename}] [--umcregistration {filename}] [--icon {filename}]` ``}`` :samp:`[--packagename {packagename}] [--packageversion {packageversion}] [--name {objectname}] [--ucsversionstart {ucsversion}] [--ucsversionend {ucsversion}]`
   The shell function :command:`ucs_registerLDAPExtension` from the Univention
   shell function library (see :ref:`misc-lib`) can be used to register several
   extension in LDAP. This shell function offers several modes:

   .. index::
      single: LDAP; schema extension

   .. option:: --schema <filename>.schema

      Register one or more LDAP schema extension (see
      :ref:`settings-ldapschema`)

   .. index::
      single: LDAP; access control list extension

   .. option:: --acl <filename>.acl

      Register one or more LDAP access control list (see
      :ref:`settings-ldapacl`)

   .. index::
      single: directory manager; syntax extension

   .. option:: --udm_syntax <filename>.py

      Register one or more UDM syntax extension (see :ref:`udm-syntax`)

   .. index::
      single: directory manager; hook extension

   .. option:: --udm_hook <filename>.py

      Register one or more UDM hook (see :ref:`udm-hook`)

   .. index::
      single: Directory manager; module extension

   .. option:: --udm_module <filename>.py

      Register a single UDM module (see :ref:`udm-modules`)

   The modes can be combined. If more than one mode is used in one call of the
   function, the modes are always processed in the order as listed above. Each
   of these options expects a filename as an required argument.

   It is possible to register different extensions to different UCS versions:

   .. option:: --name <name>

      The option can be used to supply an object name to be used to store the
      extension. If not set :file:`{filename}` will be used. If combined with
      :option:`--udm_module` the name must include a forward slash.

   .. option:: --ucsversionstart <ucsversion>

      The option can be used to supply the earliest version of UCS to which the
      UDM extension should be deployed.

   .. option:: --ucsversionend <ucsversion>

      The option can be used to supply the last version of UCS to which the UDM
      extension should be deployed. Together with ``--ucsversionstart`` and
      ``--name``, it is possible to deploy different versions of a UDM
      extension.

   The following options can be given multiple times, but only after the option
   :option:`--udm_module`:

   .. option:: --messagecatalog <prefix>/<language>.mo

      The option can be used to supply message translation files in GNU message
      catalog format. The language must be a valid language tag, i.e. must
      correspond to a subdirectory of :file:`/usr/share/locale/`.

   .. option:: --umcmessagecatalog <prefix>/<language>-<module_id>-<application_name>.mo

      Similar to the option above this option can be used to supply message
      translation files in GNU message catalog format, but for the UMC. The
      filename takes the form :file:`language-moduleid.mo`, e.g.
      :file:`de-udm.mo`, where :samp:`{language}` must be a valid language tag,
      i.e. must correspond to a subdirectory of :file:`/usr/share/locale/`. The
      :samp:`{moduleid}` is specified in the UMC registration file (see
      :ref:`umc-xml`). The MO files are then placed under
      :file:`/usr/share/univention-management-console/i18n/` in a subdirectory
      with the corresponding language short code.

   .. option:: --umcregistration <filename>.xml

      The option can be used to supply an UMC registration file (see
      :ref:`umc-xml`) to make the UDM module accessible through Univention
      Management Console (UMC).

   .. option:: --icon <filename>

      The option can be used to supply icon files (:file:`PNG` or :file:`JPEG`,
      in 16×16 or 50×50, or :file:`SVGZ`).

   .. note::

      UDM extensions will only be deployed to UCS 5 if either
      ``--ucsversionstart`` or ``--ucsversionend`` are set.

   Called from a joinscript, the function automatically determines some required
   parameters, like the app identifier plus Debian package name and version,
   required for the creation of the corresponding object. After creation of the
   object the function waits up to 3 minutes for the |UCSPRIMARYDN| to signal
   availability of the new extension and reports success or failure.

   For UDM extensions it additionally checks that the corresponding file has
   been made available in the local file system. Failure conditions may occur
   e.g. in case the new LDAP schema extension collides with the schema currently
   active. The |UCSPRIMARYDN| only activates a new LDAP schema or ACL extension
   if the configuration check succeeded.

   .. note::

      The corresponding UDM modules are documented in :ref:`chap-udm`.

   Before calling the shell, function the shell variable
   :envvar:`UNIVENTION_APP_IDENTIFIER` should be set to the versioned app
   identifier (and exported to the environment of sub-processes). The shell
   function will then register the specified app identifier with the extension
   object to indicate that the extension object is required as long as this app
   is installed anywhere in the UCS domain.

   The options ``--packagename`` and ``--packageversion`` should usually not be
   used, as these parameters are determined automatically. To prevent accidental
   downgrades the function :command:`ucs_registerLDAPExtension` (as well as the
   corresponding UDM module) only execute modifications of an existing object if
   the Debian package version is not older than the previous one.

   :command:`ucs_registerLDAPExtension` supports two additional options to
   specify a valid range of UCS versions, where an extension should be
   activated. The options are ``--ucsversionstart`` and ``--ucsversionend``. The
   version check is only performed whenever the extension object is modified. By
   calling this function from a joinscript, it will automatically update the
   Debian package version number stored in the object, triggering a
   re-evaluation of the specified UCS version range. The extension is activated
   up to and excluding the UCS version specified by ``--ucsversionend``. This
   validity range is not applied to LDAP schema extensions, since they must not
   be undefined as long as there are objects in the LDAP directory which make
   use of it.

   .. code-block:: bash
      :caption: Extension registration in join script
      :name: join-register-extensions

      $ export UNIVENTION_APP_IDENTIFIER="appID-appVersion" ## example
      $ . /usr/share/univention-lib/ldap.sh

      $ ucs_registerLDAPExtension "$@" \
        --schema /path/to/appschemaextension.schema \
        --acl /path/to/appaclextension.acl \
        --udm_syntax /path/to/appudmsyntax.py

      $ ucs_registerLDAPExtension "$@" \
        --udm_module /path/to/appudmmodule.py \
        --messagecatalog /path/to/de.mo \
        --messagecatalog /path/to/eo.mo \
        --umcregistration /path/to/module-object.xml \
        --icon /path/to/moduleicon16x16.png \
        --icon /path/to/moduleicon50x50.png


:command:`ucs_unregisterLDAPExtension` :samp:`[--binddn {bind-dn} --bindpwdfile {filename}]` ``{`` :samp:`--schema {objectname} | --acl {objectname} | --udm_syntax {objectname} | --udm_hook {objectname} | --udm_module {objectname}` ``...}``
   There is a corresponding :command:`ucs_unregisterLDAPExtension` function,
   which can be used to un-register extension objects. This only works if no app
   is registered any longer for the object. It must not be called unless it has
   been verified that no object in LDAP still requires this schema extension.
   For this reason it should generally not be called in unjoin scripts.

   .. code-block:: bash
      :caption: Schema un-registration in unjoin script
      :name: join-unregister-extensions

      . /usr/share/univention-lib/ldap.sh
      ucs_unregisterLDAPExtension "$@" --schema appschemaextension
