.. _principle-summary:

**********
Principles
**********

The following list summarizes the principles described in the document for your
reference. To jump to the location in the document for more context on the
principle, click the title of the principle.

:ref:`Principle #1 <principle-1>`
   Don't manually edit configuration files that are under control of |UCR| or
   directory listener modules.

:ref:`Principle #2 <principle-2>`
   Use the standard software packages that |UCS| installs to provide core product
   capabilities.

   Don't replace these software packages with software of your own personal
   taste.

:ref:`Principle #3 <principle-3>`
   Use the :command:`univention-*` tools to perform actions for installing,
   updating and removing software packages and apps on UCS.

:ref:`Principle #4 <principle-4>`
   Before installing software packages from third-party sources:

   #. Always verify the App Center and the standard Univention software
      repositories, if the software is already available there.

   #. Make sure that the packages don't overwrite existing packages.

   #. Use :command:`pip` only in virtual Python environments.

:ref:`Principle #5 <principle-5>`
   Don't run :command:`univention-join` on a *Primary Directory Node*. It just
   skips.

:ref:`Principle #6 <principle-6>`
   Install UCS components through the App Center.

:ref:`Principle #7 <principle-7>`
   Always verify status and version of join scripts in the following situations:

   * After installation of software or apps.
   * After updates of software or apps.
   * When services don't run as expected.

:ref:`Principle #8 <principle-8>`
   Never run :command:`univention-run-joinscripts --force` on a *Primary
   Directory Node*.

   The LDAP server doesn't work properly anymore and the repair is a lot of
   effort.
