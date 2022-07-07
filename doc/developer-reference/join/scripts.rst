.. _chap-scripts:

Join scripts
============

.. index::
   pair: domain join; join script

Packages requiring write access to the Univention directory service can provide
so called join scripts. They are installed into
:file:`/usr/lib/univention-install/`. The name of each join script is normally
derived from the name of the binary package containing it. It is prefixed with a
two-digit number, which is used to order the scripts lexicographically. The
filename either ends in :file:`.inst` or :file:`.uinst`, which distinguishes
between join script and unjoin script (see :ref:`join-unjoin`). The file must
have the executable permission bits set.
