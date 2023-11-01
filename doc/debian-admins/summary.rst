.. _summary:

*****************
Guideline summary
*****************

:ref:`Rule #1 <rule-1>`
   Don't manually edit configuration files that are under control of |UCR|.

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
