.. _summary:

****************
Summary of rules
****************

:ref:`Rule #1 <rule-1>`
   Don't manually edit configuration files that are under control of |UCR| or
   directory listener modules.

:ref:`Rule #2 <rule-2>`
   Use the standard software packages that |UCS| installs to provide core product
   capabilities.

   Don't replace these software packages with software of your own personal
   taste.

:ref:`Rule #3 <rule-3>`
   Use the :command:`univention-*` tools to perform actions for installing,
   updating and removing software packages and apps on UCS.

:ref:`Rule #4 <rule-4>`
   Before installing software packages from third-party sources:

   #. Always verify the App Center and the standard Univention software
      repositories, if the software is already available there.

   #. Make sure that the packages don't overwrite existing packages.

   #. Use :command:`pip` only in virtual Python environments.

:ref:`Rule #5 <rule-5>`
   Don't run :command:`univention-join` on a *Primary Directory Node*. It just
   skips.

:ref:`Rule #6 <rule-6>`
   Install UCS components through the App Center.

:ref:`Rule #7 <rule-7>`
   Always verify status and version of join scripts in the following situations:

   * After installation of software or apps.
   * After updates of software or apps.
   * When services don't run as expected.

:ref:`Rule #8 <rule-8>`
   Never run :command:`univention-run-joinscripts --force` on a *Primary
   Directory Node*.

   The LDAP server doesn't work properly anymore and the repair is a lot of
   effort.
