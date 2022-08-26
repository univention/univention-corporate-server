Univention Management Console
=============================

The Univention Management Console (UMC) is a service that runs on all
UCS systems by default. This service provides access to several system
information and implements modules for management tasks. What modules
are available on a UCS system depends on the system role and the
installed components. Each domain user can log on to the service via a
web interface. Depending on the access policies for the user the visible
modules for management tasks will differ.

In the following the technical details of the architecture and the
Python API for modules are described.

.. only:: internal

   .. toctree::
      :maxdepth: 3

      architecture
      protocol
      core_api
      module_api
      http
      packaging

.. only:: (not internal)

   .. toctree::
      :maxdepth: 3

      architecture
      protocol
      http
      packaging
