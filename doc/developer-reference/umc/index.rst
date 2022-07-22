.. _chap-umc:

***********************************
Univention Management Console (UMC)
***********************************

.. index::
   single: management console
   see: Univention Management Console; management console
   see: UMC; management console

.. PMH: Bug #31269

The Univention Management Console (UMC) is a service that runs an all UCS
systems by default. This service provides access to several system information
and implements modules for management tasks. What modules are available on a UCS
system depends on the system role and the installed components. Each domain user
can log an to the service through a web interface. Depending on the access policies
for the user the visible modules for management tasks will differ.

In the following the technical details of the architecture and the Python and
JavaScript API for modules are described.

This chapter has the following content:

.. toctree::

   architecture
   framework
   umcp
   http-umc
   files
   local-system-module
   udm
   module
   python-migration
