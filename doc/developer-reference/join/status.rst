.. _join-status:

Join status
===========

.. index::
   single: domain join; join status

For each join script a version number is tracked. This is used to skip
re-executing join scripts, which already have been executed. This is mostly a
performance optimization, but is also used to find join scripts which need to be
run.

The text file :file:`/var/univention-join/status` is used to keep track of the
state of all join scripts. For each successful run of a join script a line is
appended to that file. That record consists of three space separated entries:

::

   $script_name v$version successful

#. The first entry contains the name of the join script without the two-digit
   prefix and without the :file:`.inst` suffix, usually corresponding to the
   package name.

#. The second entry contains a version number prefixed by a ``v``. It is used to
   keep track of the latest version of the join script, which has been run
   successfully. This is used to identify, which join scripts need to be
   executed and which can be skipped, because they were already executed in the
   past.

#. The third column contains the word successful.

If a new version of the join script is invoked, it just appends a new record
with a higher version number at the end of the file.
