.. _chap-debian:

****************
Debian packaging
****************

.. index::
   single: packaging; debian

This chapter describes how software for |UCSUCS| is packaged in the Debian
format. It allows proper dependency handling and guarantees proper tracking of
file ownership. Customers can package their own internal software or use the
package mechanism to distribute configuration files consistently to different
machines.

Software is packaged as a *source package*, from which one or more *binary
packages* can be created. This is useful to create different packages from the
same source package. For example the :program:`Samba` source package creates
multiple binary packages:

* one containing the file server

* one containing the client commands to access the server

* and several other packages containing documentation, libraries, and common
  files shared between those packages

The directory should be named :file:`{package_name}-{version}`.

.. _deb-prerequisites:

Prerequisites and preparation
=============================

.. index::
   single: packaging; build dependencies

Some packages are required for creating and building packages.

:program:`build-essential`
   This meta package depends on several other packages like compilers and tools
   to extract and build source packages. Packages must not declare an explicit
   dependency on this and its dependent packages.

:program:`devscripts`
   This package contains additional scripts to modify source package files like
   for example :file:`debian/changelog`.

:program:`dh-make`
   This program helps to create an initial :file:`debian/` directory, which can
   be used as a starting point for packaging new software.

These packages must be installed on the development system. If not, missing
packages can be installed on the command line using
:command:`univention-install` or through UMC, which is described in the
:cite:t:`ucs-manual`.

.. _deb-dhmake:

:command:`dh_make`
==================

:command:`dh_make` is a tool, which helps creating the initial :file:`debian/`
directory. It is interactive by default and asks several questions about the
package to be created.

.. code-block::

   Type of package: single binary, indep binary, multiple binary, library, kernel module, kernel patch?
   [s/i/m/l/k/n]


:kbd:`s`, single binary
   A single architecture specific binary package is created from the source
   package. This is for software which needs to be compiled individually for
   different CPU architectures like ``i386`` and ``amd64``.

:kbd:`i`, indep binary
   A single architecture-independent binary package is created from the source
   package. This is for software which runs unmodified on all CPU architectures.

:kbd:`m`, multiple binary
   Multiple binary packages are created from the source package, which
   can be both architecture independent and dependent.

:kbd:`l`, library
   Two or more binary packages are created for a compiled library package. The
   runtime package consists of the shared object file, which is required for
   running programs using that library. The development package contains the
   header files and other files, which are only needed when compiling and
   linking programs on a development system.

:kbd:`k`, kernel module
   A single kernel-dependent binary package is created from the source package.
   Kernel modules need to be compiled for each kernel flavor. :program:`dkms`
   should probably be used instead. This type of packages is not described in
   this manual.

:kbd:`n`, kernel patch
   A single kernel-independent package is created from the source package, which
   contains a patch to be applied against an unpacked Linux kernel source tree.
   :program:`dkms` should probably be used instead. This type of packages is not
   described in this manual.

In Debian, a package normally consists of an upstream software archive, which is
provided by a third party like the Samba team. This collection is extended by a
Debian specific second TAR archive or a patch file, which adds the
:file:`debian/` directory and might also modify upstream files for better
integration into a Debian system.

When a source package is built, :manpage:`dpkg-source.1` separates the files
belonging to the packaging process from files belonging to the upstream package.
For this to work, :command:`dpkg-source` needs the original source either
provided as a TAR archive or a separate directory containing the unpacked
source. If neither of these is found and ``--native`` is not given,
:command:`dh_make` prints the following warning:

.. code-block::

   Could not find my-package_1.0.orig.tar.gz
   Either specify an alternate file to use with -f,
   or add --createorig to create one.


The warning from :command:`dh_make` states that no pristine upstream archive was
found, which prohibits the creation of the Debian specific patch, since the
Debian packaging tools have no way to separate upstream files from files
specific to Debian packaging. The option ``--createorig`` can be passed to
:command:`dh_make` to create a :file:`.orig.tar.gz` archive before creating the
:file:`debian/` directory, if such separation is required.

.. _deb-debian:

Debian control files
====================

The control files in the :file:`debian/` directory control the package
creation process. The following sections provide a short description of
these files. A more detailed description is available in the
:cite:t:`debian-pkg-basics`.

Several files will have the :file:`.ex` suffix, which mark them as examples. To
activate these files, they must be renamed by stripping this suffix. Otherwise,
the files should be deleted to not clutter up the directory by unused files. In
case a file was deleted and needs to be restored, the original templates can be
found in the :file:`/usr/share/debhelper/dh_make/debian/` directory.

The :file:`debian/` directory contains some global configuration files, which
can be put into two categories: The files :file:`changelog`, :file:`control`,
:file:`copyright`, :file:`rules` are required and control the build process of
all binary packages. Most other files are optional and only affect a single
binary package. Their filename is prefixed with the name of the binary package.
If only a single binary package is build from the source package, this prefix
can be skipped, but it is good practice to always use the prefix.

The following files are required:

:file:`changelog`
   Changes related to packaging, not the upstream package. See
   :ref:`deb-changelog` below for more information.

:file:`compat`
   The :program:`Debhelper` tools support different compatibility levels. For
   UCS-3.x the file must contain a single line with the value ``7``. See
   :manpage:`debhelper.7` for more details.

:file:`control`
   Contains control information about the source and all its binary packages.
   This mostly includes package name and dependency information. See
   :ref:`deb-control` below for more information.

:file:`copyright`
   This file contains the copyright and license information for all files
   contained in the package. See :ref:`deb-copyright` below for more
   information.

:file:`rules`
   This is a :file:`Makefile` style file, which controls the package build
   process. See :ref:`deb-rules` below for more information.

:file:`source/format`
   This file configures how :manpage:`dpkg-source.1` separates the files
   belonging to the packaging process from files belonging to the upstream
   package. Historically, the Debian source format ``1.0`` shipped packages as a
   TAR file containing the upstream source plus one patch file, which contained
   all files of the :file:`debian/` sub-directory in addition to all changes to
   upstream files.

   The new format ``3.0 (quilt)`` replaces the patch file with a second TAR
   archive containing the :file:`debian/` directory. Changes to upstream files
   are no longer applied as one giant patch, but split into logical changes and
   applied using a built-in :manpage:`quilt.1`.

   For simple packages, where there is no distinction between upstream and the
   packaging entity, the ``3.0 (native)`` format can be used instead, were all
   files including the :file:`debian/` directory are contained in a single TAR
   file.

The following files are optional and should be deleted if unused, which helps
other developers to concentrate on only the files relevant to the packaging
process:

:file:`README.Debian`
   Notes regarding package specific changes and differences to default
   options, for example compiler options. Will be installed into
   :file:`/usr/share/doc/{package_name}/README.Debian`.

:file:`{package}.cron.d`
   Cron tab entries to be installed. See :manpage:`dh_installcron.1` for more
   details.

:file:`{package}.dirs`
   List of extra directories to be created. See :manpage:`dh_installdirs.1` for
   more details. May other :command:`dh_` tools automatically create directories
   themselves, so in most cases this file is unneeded.

:file:`{package}.install`
   List of files and directories to be copied into the package. This is normally
   used to partition all files to be installed into separate packages, but can
   also be used to install arbitrary files into packages. See
   :manpage:`dh_install.1` for more details.

:file:`{package}.docs`
   List of documentation files to be installed in
   :file:`/usr/share/doc/{package}/`. See :manpage:`dh_installdocs.1` for more
   details.

:file:`{package}.emacsen-install`; :file:`{package}.emacsen-remove`; :file:`{package}.emacsen-startup`
   Emacs specific files to be installed below
   :file:`/usr/share/emacs-common/{package}/`. See
   :manpage:`dh_installemacsen.1` for more details.

:file:`{package}.doc-base*`
   Control files to install and register extended HTML and PDF documentation.
   See :manpage:`dh_installdocs.1` for more details.

:file:`{package}.init.d`; :file:`{package}.default`
   Start-/stop script to manage a system daemon or service. See
   :manpage:`dh_installinit.1` for more details.

:file:`{package}.manpage.{1}`; :file:`{package}.manpage.sgml`
   Manual page for programs, library functions or file formats, either directly
   in :command:`troff` or SGML. See :manpage:`dh_installman.1` for more details.

:file:`{package}.menu`
   Control file to register programs with the Debian menu system. See
   :manpage:`dh_installmenu.1` for more details.

:file:`watch`
   Control file to specify the download location of this upstream package. This
   can be used to check for new software versions. See :manpage:`uscan.1` for
   more details.

:file:`{package}.preinst`; :file:`{package}.postinst`; :file:`{package}.prerm`; :file:`{package}.postrm`
   Scripts to be executed before and after package installation and removal. See
   :ref:`deb-scripts` below for more information.

:file:`{package}.maintscript`
   Control file to simplify the handling of configuration files. See
   :manpage:`dpkg-maintscript-helper.1` and :manpage:`dh_installdeb.1` for more
   information.

Other :program:`debhelper` programs use additional files, which are described in
the respective manual pages.

.. _deb-control:

:file:`debian/control`
----------------------

The :file:`control` file contains information about the packages and their
dependencies, which are needed by :command:`dpkg`. The initial :file:`control`
file created by :command:`dh_make` looks like this:

.. code-block::

   Source: testdeb
   Section: unknown
   Priority: optional
   Maintainer: John Doe <user@example.com>
   Build-Depends: debhelper (>= 5.0.0)
   Standards-Version: 3.7.2

   Package: testdeb
   Architecture: any
   Depends: ${shlibs:Depends}, ${misc:Depends}
   Description: <insert up to 60 chars description>
   <insert long description, indented with spaces>


The first block beginning with ``Source`` describes the source package:

``Source``
   The name of the source package. Must be consistent with the directory name of
   the package and the information in the :file:`changelog` file.

`Section <debian-policy-subsection_>`_
   A category name, which is used to group packages. There are many predefined
   categories like ``libs``, ``editors``, ``mail``, but any other string can be
   used to define a custom group.

`Priority <debian-policy-priority_>`_
   Defines the priority of the package. This information is only used by some
   tools to create installation DVD. More important packages are put on earlier
   CD, while less important packages are put on later CD.

   ``essential``
      Packages are installed by default and :command:`dpkg` prevents the user
      from easily removing it.

   ``required``
      Packages which are necessary for the proper functioning of the system. The
      package is part of the base installation.

   ``important``
      Important programs, including those which one would expect to find on any
      Unix-like system. The package is part of the base installation.

   ``standard``
      These packages provide a reasonably small but not too limited
      character-mode system.

   ``optional``
      Package is not installed by default. This level is recommended for most
      packages.

   ``extra``
      This contains all packages that conflict with some other packages.

``Maintainer``
   The name and email address of a person or group responsible for the
   packaging.

``Build-Depends``; ``Build-Depends-Indep``
   A list of packages which are required for building the package.

``Standards-version``
   Specifies the Debian Packaging Standards version, which this package is
   conforming to. This is not used by UCS, but required by Debian.

All further blocks beginning with ``Package`` describes a binary package. For
each binary package one block is required.

``Package``
   The name of the binary package. The name must only consist of lower case
   letters, digits and dashes. If only a single binary package is built from a
   source package, the name is usually the same as the source package name.

``Architecture``
   Basically there are two types of packages:

   * Architecture dependent packages must be build for each architecture like
     ``i386`` and ``amd64``, since binaries created on one architecture do not
     run on other architectures. A list of architectures can be explicitly
     given, or ``any`` can be used, which is then automatically replaced by the
     architecture of the system where the package is built.

   * Architecture independent packages only need to be built once, but can be
     installed on all architectures. Examples are documentation, scripts and
     graphics files. They are declared using ``all`` in the architecture field.

``Description``
   The first line should contain a short description of up to 60 characters,
   which should describe the purpose of the package sufficiently. A longer
   description can be given after that, where each line is indented by a single
   space. An empty line can be inserted by putting a single dot after the
   leading space.

Most packages are not self-contained but need other packages for proper
function. Debian supports different kinds of dependencies.

``Depends``
   A essential dependency on some other packages, which must be already
   installed and configured before this package is configured.

``Recommends``
   A strong dependency on some other packages, which should normally be
   co-installed with this package, but can be removed. This is useful for
   additional software like plug-ins, which extends the functionality of this
   package, but is not strictly required.

``Suggests``
   A soft dependency on some other packages, which are not installed by default.
   This is useful for additional software like large add-on packages and
   documentation, which extends the functionality of this package, but is not
   strictly required.

``Pre-Depends``
   A strong dependency on some other package, which must be fully operational
   even before this package is unpacked. This kind of dependency should be used
   very sparsely. It's mostly only required for software called from the
   :file:`.preinst` script.

``Conflicts``
   A negative dependency, which prevents the package to be installed while the
   other package is already installed. This should be used for packages, which
   contain the same files or use the same resources, for example TCP port
   numbers.

``Provides``
   This package declares, that it provides the functionality of some other
   package and can be considered as a replacement for that package.

``Replaces``
   A declaration, that this package overwrites the files contained in some other
   package. This deactivates the check normally done by :command:`dpkg` to
   prevent packages from overwriting files belonging to some other package.

``Breaks``
   A negative dependency, which requests the other package to be upgraded before
   this package can be installed. This is a lesser form of ``Conflicts``.
   ``Breaks`` is almost always used with a version specification in the form
   :samp:`Breaks: {package} (<< {version})`: This forces :samp:`package`
   to be upgraded to a version greater than :samp:`{version}` before this
   package is installed.

In addition to literal package names, :program:`debhelper` supports a
substitution mechanism: Several helper scripts are capable of automatically
detecting dependencies, which are stored in variables.

``${shlibs:Depends}``
   :command:`dh_shlibdeps` automatically determines the shared library used by
   the programs and libraries of the package and stores the package names
   providing them in this variable.

``${python:Depends}``
   :command:`dh_python` detects similar dependencies for Python modules.

``${misc:Depends}``
   Several :program:`Debhelper` commands automatically add additional
   dependencies, which are stored in this variable.

In addition to specifying a single package as a dependency, multiple packages
can be separated by using the pipe symbol (``|``). At least one of those
packages must be installed to satisfy the dependency. If none of them is
installed, the first package is chosen as the default.

A package name can be followed by a version constraint enclosed in parenthesis.
The following operators are valid:

``<<``
   is less than

``<=``
   is less than or equal to

``=``
   is equal to

``>=``
   is greater than or equal to

``>>``
   is greater than

For example:

.. code-block::

   Depends: libexample1 (>= ${binary:Version}),
    exim4 | mail-transport-agent,
    ${shlibs:Depends}, ${misc:Depends}
   Conflicts: libgg0, libggi1
   Recommends: libncurses5 (>> 5.3)
   Suggests: libgii0-target-x (= 1:0.8.5-2)
   Replaces: vim-python (<< 6.0), vim-tcl (<= 6.0)
   Provides: www-browser, news-reader


.. _deb-copyright:

:file:`debian/copyright`
------------------------

The :file:`copyright` file contains copyright and license information. For a
downloaded source package it should include the download location and names of
upstream authors.

::

   This package was debianized by John Doe <max@example.com> on
   Mon, 21 Mar 2009 13:46:39 +0100.

   It was downloaded from <fill in ftp site>

   Copyright:
   Upstream Author(s): <put author(s) name and email here>

   License:
   <Must follow here>


The file does not require any specific format. Debian recommends to use a
machine-readable format, but this is not required for UCS. The format is
described in `Machine-readable debian/copyright file
<debian-dep5_>`_ at looks like this:

::

   Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
   Upstream-Name: Univention GmbH
   Upstream-Contact: <package>@univention.de>
   Source: https://docs.software-univention.de/

   Files: *
   Copyright: 2013-2022 Univention GmbH
   License: AGPL


.. _deb-changelog:

:file:`debian/changelog`
------------------------

The :file:`changelog` file documents the changes applied to this Debian package.
The initial file created by :command:`dh_make` only contains a single entry and
looks like this:

::

   testdeb (0.1-1) unstable; urgency=low

     * Initial Release.

    -- John Doe <user@example.com>  Mon, 21 Mar 2013 13:46:39 +0100


For each new package release a new entry must be prepended before all previous
entries. The version number needs to be incremented and a descriptive text
should be added to describe the change.

The command :command:`debchange` from the :program:`devscripts` package can be
used for editing the :file:`changelog` file. For example the following command
adds a new version:

::

   dch -i

After that the :file:`changelog` file should look like this:

::

   testdeb (0.1-2) unstable; urgency=low

     * Add more details.

    -- John Doe <user@example.com>  Mon, 21 Mar 2013 17:55:47 +0100

   testdeb (0.1-1) unstable; urgency=low

     * Initial Release.

    -- John Doe <user@example.com>  Mon, 21 Mar 2013 13:46:39 +0100


The date and timestamp must follow the format described in :rfc:`2822`.
:command:`debchange` automatically inserts and updates the current date.
Alternatively :command:`date -R` can be used on the command line to create the
correct format.

For UCS it is best practice to mention the bug ID of the UCS bug tracker (see
:ref:`chap-bug`) to reference additional details of the bug fixed. Other parties
are encouraged to devise similar comments, for example URLs to other bug
tracking systems.

.. _deb-rules:

:file:`debian/rules`
--------------------

The file :file:`rules` describes the commands needed to build the package. It
must use the :program:`Make` syntax :cite:t:`make`. It consists of several
rules, which have the following structure:

.. code:: make

   target: dependencies
       command
       ...


Each rule starts with the target name, which can be a filename or symbolic name.
Debian requires the following targets:

``clean``
   This rule must remove all temporary files created during package build and
   must return the state of all files back to the same state as when the package
   is freshly extracted.

``build``; ``build-arch``; ``build-indep``
   These rules should configure the package and build either all, all
   architecture dependent or all architecture independent files.

   These rules are called without root permissions.

``binary``; ``binary-arch``; ``binary-indep``
   These rules should install the package into a temporary staging area. By
   default this is the directory :file:`debian/tmp/` below the source package
   root directory. From there files are distributed to individual packages,
   which are created as the result of these rules.

   These rules are called with root permissions.

Each command line must be indented with one tabulator character. Each command is
executed in a separate shell, but long command lines can be split over
consecutive lines by terminating each line with a backslash (``\``).

Each rule describes a dependency between the target and its dependencies.
:command:`make` considers a target to be out-of-date, when a file with that name
:file:`target` does not exists or when the file is older than one of the files
it depends on. In that case :command:`make` invokes the given commands to
re-create the target.

In addition to filenames also any other word can be used for target names and in
dependencies. This is most often used to define *phony* targets, which can be
given on the command line invocation to trigger some tasks. The above mentioned
``clean``, ``build`` and ``binary`` targets are examples for that kind of
targets.

:command:`dh_make` only creates a template for the :file:`rules` file. The
initial content looks like this:

::

   #!/usr/bin/make -f
   # -*- makefile -*-
   # Sample debian/rules that uses debhelper.
   # This file was originally written by Joey Hess and Craig Small.
   # As a special exception, when this file is copied by dh-make into a
   # dh-make output file, you may use that output file without restriction.
   # This special exception was added by Craig Small in version 0.37 of dh-make.

   # Uncomment this to turn on verbose mode.
   #export DH_VERBOSE=1

   %:
       dh $@


Since UCS-3.0 the :file:`debian/rules` file is greatly simplified by using the
:command:`dh` sequencer. It is a wrapper around all the different
:program:`debhelper` tools, which are automatically called in the right order.

.. tip::

   To exactly see which commands are executed when :command:`dpkg-buildpackage`
   builds a package, invoke :samp:`dh {target} --no-act` by hand, for example
   :command:`dh binary --no-act` lists all commands to configure, build, install
   and create the package.

In most cases it's sufficient to just provide additional configuration files for
the individual :program:`debhelper` commands as described in :ref:`deb-debian`.
If this is not sufficient, any :program:`debhelper` command can be individually
overridden by adding an *override* target to the :file:`rules` file.

For example the following snippet disables the automatic detection of the build
system used to build the package and passes additional options:

.. code:: make

   override_dh_auto_configure:
       ./setup --prefix=/usr --with-option-foo


Without that explicit override :command:`dh_auto_configure` would be called,
which normally automatically detects several build systems like
:program:`cmake`, :program:`setup.py`, :program:`autoconf` and others. For these
:command:`dh` also passes the right options to configure the default prefix
:file:`/usr` and use the right compiler flags.

After configuration the package is built and installed to the temporary staging
area in :file:`debian/tmp/`. From there :command:`dh_install` partitions
individual files and directories to binary packages. This is controlled through
the :file:`debian/{package}.install` files.

This file can also be used for simple packages, where no build system is used.
If a path given in the :file:`debian/{package}.install` file is not found below
:file:`debian/tmp/`, the path is interpreted as relative to the source package
root directory. This mechanism is sufficient to install simple files, but fails
when files must be renamed or file permissions must be modified.

.. _deb-scripts:

:file:`debian/preinst`, :file:`debian/prerm`, :file:`debian/postinst`, :file:`debian/postrm`
--------------------------------------------------------------------------------------------

In addition to distributing only files, packages can also be used to run
arbitrary commands on installation, upgrades or removal. This is handled by the
four *Maintainer scripts*, which are called before and after files are unpacked
or removed:

:file:`debian/{package}.preinst`
   called before files are unpacked.

:file:`debian/{package}.postinst`
   called after files are unpacked. Mostly used to (re-)start services after
   package installation or upgrades.

:file:`debian/{package}.prerm`
   called before files are removed. Mostly used to stop services before a
   package is removed or upgraded.

:file:`debian/{package}.postrm`
   called after files have been removed.

The scripts themselves must be shell scripts, which should contain a
``#DEBHELPER#`` marker, where the shell script fragments created by the
:command:`dh_` programs are inserted. Each script is invoked with several
parameters, from which the script can determine, if the package is freshly
installed, upgraded from a previous version, or removed. The exact arguments are
described in the template files generated by :command:`dh_make`.

The maintainer scripts can be called multiple times, especially when errors
occur. Because of that the scripts should be idempotent, that is they should be
written to *achieve a consistent state* instead of blindly doing the same
sequence of commands again and again.

A bad example would be to append some lines to a file on each invocation. The
right approach would be to add a check, if that line was already added and only
do it otherwise.

.. warning::

   Make sure to handle package *upgrades* and *removal* correctly: Both tasks
   will invoke any existing scripts :file:`prerm` and :file:`postrm`, but with
   different parameters ``remove`` and ``upgrade`` only.

   It is important that all these scripts handle error conditions properly:
   Maintainer scripts should exit with :command:`exit 0` on success and
   :command:`exit 1` on fail, if things go catastrophically wrong.

   On the other hand, an exit code unequal to zero usually aborts any package
   installation, upgrade or removal process. This prevents any automatic package
   maintenance and usually requires manual intervention of a human
   administrator. Therefore, it is essential that maintainer scripts handle
   error conditions properly and are able to recover an inconsistent state.

.. _deb-build:

Building
========

Before the first build is started, remove all unused files from the
:file:`debian/` directory. This simplifies maintenance of the package and helps
other maintainers to concentrate on only the relevant differences from standard
packages.

The build process is started by invoking the following command:

.. code-block:: console

   $ dpkg-buildpackage -us -uc

The options ``-us`` and ``-uc`` disable the PGP signing process of the source
and changes files. This is only needed for Debian packages, were all files must
be cryptographically signed to be uploaded to the Debian infrastructure.

Additionally, the option ``-b`` can be added to restrict the build process to
only build the binary packages. Otherwise a source package will also be created.

.. _deb-links:

Further reading
===============

* :cite:t:`debian-pkg-basics`

* :cite:t:`debian-maint-guide`

* :cite:t:`debian-policy`

* :cite:t:`debian-dev-ref`
