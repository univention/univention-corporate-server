.. _chap-packaging:

******************
Packaging software
******************

.. index::
   single: packaging

.. highlight:: console

This chapter describes how software for UCS is packaged. For more
details on packaging software in the Debian format, see
:ref:`chap-debian`.

.. _pkg-introduction:

Introduction
============

UCS is based on the Debian distribution, that uses the deb format to package
software. The program :command:`dpkg` is used for handling a set of packages. On
installation packages are unpacked and configured, while on un-installation
packages are de-configured and the files belonging to the packages are removed
from the system.

On top of that the :program:`apt`-tools provide a software repository, which
allows software to be downloaded from central file servers.

:file:`Package` files provide an index of all packages contained in the
repository, which is used to resolve dependencies between packages. While
:command:`dpkg` works on a set of packages given on the command line,
:command:`apt-get` builds that set of packages and their dependencies before
invoking :command:`dpkg` on this set. :command:`apt-get` is a command line tool,
which is fully described in its manual page :manpage:`apt-get(8)`. A more modern version with
a text based user interface is :command:`aptitude`, while :command:`synaptic`
provides a graphical front end.

On UCS systems the administrator is not supposed to use these tools
directly. Instead all software maintenance can be done through the UMC,
which maps the requests to invocations of the commands given above.

.. _pkg-preparation:

Preparations
============

This chapter describes some simple examples using existing packages. For
downloading and building them, some packages must be installed on the system
used as a development system:

* :program:`git` is used to checkout the source files belonging to the packages.

* :program:`build-essential` must be installed for building the package.

* :program:`devscripts` provides some useful tools for maintaining packages.

This can be achieved by running the following command:

.. code-block::

   $ sudo apt-get install git build-essential devscripts

.. _pkg-rebuild:

Example: Re-building an UCS package
===================================

.. index::
   single: packaging; modify existing package

Source code:
:uv:src:`doc/developer-reference/packaging/testdeb/`

.. _pkg-procedure:

Checking out and building a UCS package
---------------------------------------

#. Create the top level working directory

   .. code-block::

      $ mkdir work
      $ cd work/

#. Either fetch the latest source code from the GIT version control system or
   download the source code of the currently packaged version.

   * Checkout example package from GIT version control system:

     .. code-block::

        $ git clone https://github.com/univention/univention-corporate-server.git
        $ cd univention-corporate-server/base/univention-ssh

   * Fetch the source code from the Univention Repository server:

     a. Enable the source repository once:

        .. code-block::

           $ sudo ucr set repository/online/sources=yes
           $ sudo apt-get update

     b. Fetch source code:

        .. code-block::

           $ apt-get source univention-ssh
           $ cd univention-ssh-*/

#. Increment the version number of package to define a newer package:

   .. code-block::

      $ debchange --local work 'Private package rebuild'


#. Install the required build dependencies

   .. code-block::

      $ sudo apt-get build-dep .

#. Build the binary package

   .. code-block::

      $ dpkg-buildpackage -uc -us -b -rfakeroot

#. Locally install the new binary package

   .. code-block::

      $ sudo apt-get install ../univention-ssh_*_*.deb


.. _pkg-new:

Example: Creating a new UCS package
===================================

.. index::
   single: packaging; new package

The following example provides a walk-through for packaging a Python script
called :file:`testdeb.py`. It creates a file :samp:`testdeb-{DATE}-{time}` in
the :file:`/tmp/` directory.

A directory needs to be created for each source package, which hosts all
other files and sub-directories.

.. code-block::

   $ mkdir testdeb-0.1
   $ cd testdeb-0.1


The file :file:`testdeb.py`, which is the program to be
installed, will be put into that directory.

.. code-block:: python

   #!/usr/bin/python3
   """
   Example for creating UCS packages.
   """

   from datetime import datetime

   if __name__ == "__main__":
      now = datetime.now()
      filename = "/tmp/testdeb-{:%y%m%d%H%M}".format(now)
      with open(filename, "a") as tmpfile:
         pass

In addition to the files to be installed, some metadata needs to be created in
the :file:`debian/` sub-directory. This directory contains several files, which
are needed to build a Debian package. The files and their format will be
described in the following sections.

To create an initial :file:`debian/` directory with all template files, invoke
the :manpage:`dh_make(1)` command provided by the package :program:`dh-make`:

.. code-block::

   $ dh_make --native --single --email user@example.com

Here several options are given to create the files for a source package,
which contains all files in one archive and only creates one binary
package at the end of the build process. More details are given in
:ref:`deb-dhmake`.

The program will output the following information:

.. code-block::

   Maintainer name  : John Doe
   Email-Address    : user@example.com
   Date             : Thu, 28 Feb 2013 08:11:30 +0100
   Package Name     : testdeb
   Version          : 0.1
   License          : blank
   Type of Package  : Single
   Hit <enter> to confirm:


The package name :program:`testdeb` and version ``0.1`` were determined from the
name of the directory :file:`testdeb-0.1`, the maintainer name and address were
gathered from the UNIX account information.

After pressing the :kbd:`Enter` key some warning message will be shown:

::

   Currently there is no top level Makefile. This may require additional
   tuning. Done. Please edit the files in the debian/ subdirectory now.
   You should also check that the testdeb Makefiles install into $DESTDIR
   and not in / .


Since this example is created from scratch, the missing
:file:`Makefile` is normal and this warning can be
ignored. Instead of writing a :file:`Makefile` to
install the single executable, :command:`dh_install` will be
used later to install the file.

Since the command completed successfully, several files were created in
the :file:`debian/` directory. Most of
them are template files, which are unused in this example. To improve
understandability they are deleted:

.. code-block::

   $ rm debian/*.ex debian/*.EX
   $ rm debian/README* debian/doc


The remaining files are required and control the build process of all
binary packages. Most of them don't need to be modified for this
example, but others must be completed using an editor.

:file:`debian/control`
   The file contains general information about the source and binary
   packages. It needs to be modified to include a description and
   contain the right build dependencies:

   .. code-block::

      Source: testdeb
      Section: univention
      Priority: optional
      Maintainer: John Doe <user@example.com>
      Build-Depends:
        debhelper-compat (= 12),
      Standards-Version: 4.3.0.3

      Package: testdeb
      Architecture: all
      Depends: ${misc:Depends}
      Description: An example package for the developer guide
       This purpose of this package is to describe the structure of a Debian
       packages. It also documents
       .
        * the structure of a Debian/Univention package
        * installation process.
        * content of packages
        * format and function of control files
       .
       For more information about UCS, refer to:
       https://www.univention.de/

:file:`debian/rules`
   This file has a :program:`Makefile` syntax and controls the package build
   process. Because there is no special handling needed in this example, the
   default file can be used unmodified.

   .. code-block:: makefile

      #!/usr/bin/make -f
      %:
      	dh $@

   .. note:: Tabulators must be used for indentation in this file.

:file:`debian/testdeb.install`
   To compensate the missing :file:`Makefile`, :manpage:`dh_install(1)` is used
   to install the executable. :command:`dh_install` is indirectly called by
   :command:`dh` from the :file:`debian/rules` file. To install the program into
   :file:`/usr/bin/`, the file needs to be created manually containing the
   following single line:

   .. code-block::

      testdeb.py usr/bin/

   .. note:: The path is not absolute, but relative.

:file:`debian/testdeb.postinst`
   Since for this example the program should be invoked automatically during
   package installation, this file needs to be created. In addition to just
   invoking the program shipped with the package itself, it also shows how
   |UCSUCRV|\ s can be set. For more information, see :ref:`ucr-usage-shell`.

   .. code-block:: shell

      #! /bin/sh
      set -e

      case "$1" in
      configure)
      	# invoke sample program
      	testdeb.py
      	# Set UCR variable if previously unset
      	ucr set repository/online/server?https://updates.software-univention.de/
      	# Force UCR variable on upgrade from previous package only
      	if dpkg --compare-versions "$2" lt-nl 0.1-2
      	then
      		ucr set timeserver1=time.fu-berlin.de
      	fi
      	;;
      abort-upgrade|abort-remove|abort-deconfigure)
      	;;
      *)
      	echo "postinst called with unknown argument \`$1'" >&2
      	exit 1
      	;;
      esac

      #DEBHELPER#

      exit 0

:file:`debian/changelog`
   The file is used to keep track of changes done to the packaging. For
   this example the file should look like this:

   .. code-block::

      testdeb (0.1-1) unstable; urgency=low

        * Initial Release.

       -- John Doe <user@example.com>  Mon, 21 Mar 2013 13:46:39 +0100

:file:`debian/copyright`
   This file is used to collect copyright related information. It is
   critical for Debian only, which need this information to guarantee
   that the package is freely re-distributable. For this example the file
   remains unchanged.

   The :file:`copyright` and
   :file:`changelog` file are installed to the
   :file:`/usr/share/doc/testdeb/`
   directory on the target system.

:file:`debian/source/format`
   This file control some internal aspects of the package build process.
   It can be ignored for the moment and are further described in
   :ref:`deb-debian`.

Now the package is ready and can be built by invoking the following
command:

.. code-block::

   $ dpkg-buildpackage -us -uc

The command should then produce the following output:

.. code-block::

   dpkg-buildpackage: info: source package testdeb
   dpkg-buildpackage: info: source version 0.1-1
   dpkg-buildpackage: info: source distribution unstable
   dpkg-buildpackage: info: source changed by John Doe <user@example.com>
   dpkg-buildpackage: info: host architecture amd64
    dpkg-source --before-build .
    debian/rules clean
   dh clean
      dh_clean
    dpkg-source -b .
   dpkg-source: info: using source format '1.0'
   dpkg-source: warning: source directory 'testdeb' is not <sourcepackage>-<upstreamversion> 'testdeb-0.1'
   dpkg-source: info: building testdeb in testdeb_0.1-1.tar.gz
   dpkg-source: info: building testdeb in testdeb_0.1-1.dsc
    debian/rules build
   dh build
      dh_update_autotools_config
      dh_autoreconf
      create-stamp debian/debhelper-build-stamp
    debian/rules binary
   dh binary
      dh_testroot
      dh_prep
      dh_install
      dh_installdocs
      dh_installchangelogs
      dh_perl
      dh_link
      dh_strip_nondeterminism
      dh_compress
      dh_fixperms
      dh_missing
      dh_installdeb
      dh_gencontrol
      dh_md5sums
      dh_builddeb
   dpkg-deb: building package 'testdeb' in '../testdeb_0.1-1_all.deb'.
    dpkg-genbuildinfo
    dpkg-genchanges  >../testdeb_0.1-1_amd64.changes
   dpkg-genchanges: info: including full source code in upload
    dpkg-source --after-build .
   dpkg-buildpackage: info: full upload; Debian-native package (full source is included)


The binary package file :file:`testdeb_0.1-1_all.deb` is stored in the parent
directory. When it is installed manually using :command:`dpkg -i
../testdeb_0.1-2_all.deb` as ``root``, the Python script is installed as
:file:`/usr/bin/testdeb.py`. It is automatically invoked by the :file:`postint`
script, so a file named :samp:`/tmp/testdeb-{date}-{time}` has been created,
too.

Congratulations! You've successfully built your first own Debian package.

.. _pkt-repository:

Setup repository
================

.. index::
   seealso: repository; packaging
   single: packaging; package repository

Until now the binary package is only available locally, thus for installation it
needs to be copied manually to each host and must be installed manually using
:command:`dpkg -i`. If the package requires additional dependencies, the
installation process will cancel, since packages are not downloaded by
:command:`dpkg`, but by :command:`apt`. To support automatic installation and
dependency resolution, the package must locate i an :program:`apt` repository,
that is available through ``http`` or some other mechanism.

For this example the repository is created below :file:`/var/www/repository/`,
which is exported by default on all UCS systems, where :program:`apache2` is
installed. Below that directory several other sub-directories and files must be
created to be compatible with the :program:`UCS Updater`. The following example
commands create a repository for UCS version 5.0 with the component name
:samp:`{testcomp}`:

.. code-block::

   $ WWW_BASE="/var/www/repository/5.0/maintained/component"
   $ TESTCOMP="testcomp/all"
   $ install -m755 -d "$WWW_BASE/$TESTCOMP"
   $ install -m644 -t "$WWW_BASE/$TESTCOMP" *.deb
   $ ( cd "$WWW_BASE"
   > rm -f "$TESTCOMP/Packages"*
   > apt-ftparchive packages "$TESTCOMP" > "Packages"
   > gzip -9 < "Packages" > "$TESTCOMP/Packages.gz"
   > mv "Packages" "$TESTCOMP/Packages" )


This repository can be included on any UCS system by appending the following
line to :file:`/etc/apt/sources.list`, assuming the FQDN of the host providing
the repository is named :samp:`{repository.server}`:

.. code-block:: debsources

   deb [trusted=yes] http://repository.server/repository/5.0/maintained/component testcomp/all/

.. note::

   It is important that the directory, from were the :command:`apt-ftparchive`
   command is invoked, matches the first string given in the
   :file:`sources.list` file after the ``deb`` prefix. The URL together with the
   suffix ``testcomp/all/`` not only specifies the location of the
   :file:`Packages` file, but is also used as the base URL for all packages
   listed in the :file:`Packages` file.

Instead of editing the :file:`sources.list` file directly, the repository can
also be included as a component, which can be configured by setting several UCR
variables. As UCR variables can also be configured through UDM policies, this
simplifies the task of installing packages from such a repository on many hosts.
For the repository above the following variables need to be set:

.. index::
   single: config registry; repository

.. code-block:: console

   $ ucr set \
   > repository/online/component/testcomp=yes \
   > repository/online/component/testcomp/server=repository.server \
   > repository/online/component/testcomp/prefix=repository

.. _pkg-obs:

Building packages through the openSUSE Build Service
====================================================

The openSUSE Build Service (OBS) is a framework to generate packages for a wide
range of distributions. Additional information can be found at
`OpenSUSE Build Service <open-suse-build-service_>`_.

If OBS is already used to build packages for other distributions, it can also be
used for |UCSUCS| builds. The build target for UCS 4.4 is called *Univention UCS
4.4*. Note that OBS doesn't handle the integration steps described in later
chapters, for example the use of |UCSUCR| templates.
