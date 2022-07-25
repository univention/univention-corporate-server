.. _chap-updater:

******************
Univention Updater
******************

.. index::
   single: updater; system update
   see: update; updater
   see: upgrade; updater

The Univention Updater is used for updating the software. It is based on the
Debian APT tools. On top of that the updater provides some UCS specific
additions.

.. _updater-repositories:

Separate repositories
=====================

.. index::
   single: updater; repositories

UCS releases are provided either through ISO images or through online
repositories. For each major, minor and patchlevel release there is a separate
online repository. They are automatically added to the files in
:file:`/etc/apt/sources.list.d/` depending on the |UCSUCRV|\ s
:envvar:`version/version` and :envvar:`version/patchlevel`, which are managed by
the updater.

Separate repositories are used to prevent automatic updates of software
packages. This is done to encouraged users to thoroughly test a new release
before their systems are updated. The only exception from this rule are the
errata updates, which are put into a single repository, which is updated
incrementally.

Therefore, the updater will include the repositories of a new release in a file
called :file:`/etc/apt/sources.list.d/00_ucs_temporary_installation.list` and
then do the updates. Only at the end of a successful update are the |UCSUCRV|\ s
updated.

Additional components can be added as separate repositories using |UCSUCRV|\ s
:samp:`repository/online/component/…`, which are described in
:ref:`chap-repoadd` and manual. Setting the variable :samp:`…/version` can be
used to mark a component as required (for certain UCS versions), which blocks an
upgrade until the component is available for the specific release(es).

If configured and enabled, components are considered required if the variable
:samp:`…/version` is unset or set to ``current``.

As an alternative a fixed list of :samp:`{$major}.{$minor}` releases can be used
to include the component only for a sub-set of releases: such a component is
only used locally if the listed component versions include the current version,
for example a ``5.0 5.1 5.2`` component will not be used on a ``5.4`` system.

.. _updater-scripts:

Updater scripts
===============

.. index::
   single: updater; scripts
   pair: preup; updater
   pair: postup; updater

In addition to the regular Debian Maintainer Scripts (see :ref:`deb-scripts`)
the UCS updater supports additional scripts, which are called before and after
each release update. Each UCS release and each component can include its own set
of scripts.

:file:`preup.sh`
   These scripts are called before the update is started. If any of the scripts
   aborts with an exit value unequal zero, the update is canceled and never
   started. The scripts receives the version number of the next release as an
   command line argument.

   For components their :file:`preup.sh` scripts is called twice:

   * Before the main release :file:`preup.sh` script is called
   * After the main script was called.

   This is indicated by the additional command line argument ``pre``
   respectively ``post``, which is *inserted before* the version string.

:file:`postup.sh`
   These scripts are called after the update successfully completed. If
   any of the scripts aborts with an exit value unequal zero, the update
   is canceled and does not finish successfully. The scripts receives
   the same arguments as described above.

The scripts are located in the :file:`all/` component of each release and
component. For UCS-5.0 this would be :file:`dists/ucs500/preup.sh` and
:file:`5.0/maintained/components/{some-component}/all/preup.sh` for the
:file:`preup.sh` script. The same applies to the :file:`postup.sh` script. The
full process is shown in :ref:`updater-release-update`.

.. _updater-scripts-signature:

Digital signature
-----------------

From UCS 3.2 on the scripts must be digitally signed by an PGP (Pretty Good
Privacy) key stored in the key-ring of :manpage:`apt-key.8`. The detached
signature must be placed in a separate file next to each updater scripts with
the additional filename extension :file:`.gpg`, that is :file:`preup.sh.gpg`
and :file:`postup.sh.gpg`. These extra files are downloaded as well and any
error in doing so and in the validation process aborts the updater immediately.

The signatures must be updated after each change to the underlying scripts. This
can be automated or be done manually with a command like the following:
:samp:`gpg -a -u {key-id} --passphrase-file {key-phrase-file} -o {script}.sh.gpg
-b {script}.sh`

Signatures can be checked manually using the following command: :samp:`apt-key
verify {script}.sh.gpg {script}.sh`

.. _updater-release-update:

Release update walkthrough
==========================

For an release update, the following steps are performed. It assumes a single
component is enabled. If multiple components are enabled, the order in which
their scripts are called is unspecified. It shows which scripts are called in
which order with which arguments.

#. Create temporary source list file :file:`00_ucs_temporary_installation.list`

#. Download the :file:`preup.sh` and :file:`postup.sh` files for the next
   release and all components into a temporary directory and validate their PGP
   signatures

#. Execute :command:`component-preup.sh pre $version`

#. Execute :command:`release-preup.sh $version`

#. Execute :command:`component-preup.sh post $version`

#. Download the new :file:`Packages` and :file:`Release` files. Their PGP
   signatures validated by :program:`APT` internally.

#. Perform the update

#. Set the release related |UCSUCRV|\ s to the new version

#. Execute :command:`component-postup.sh pre $version`

#. Execute :command:`release-postup.sh $version`

#. Execute :command:`component-postup.sh post $version`
