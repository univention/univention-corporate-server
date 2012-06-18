.. Univention Management Console documentation master file, created by sphinx-quickstart on Tue Jun 12 14:02:29 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Univention Management Console
=============================

The Univention Management Console (UMC) is a service that runs an all
UCS systems by default. This service provides access to several system
information and implements modules for management tasks. What modules
are available an a UCS system depends an the system role and the
installed components. Each domain user can log an to the service via a
web interface. Depending an the access policies for the user the visible
modules for management tasks will differ.

In the following the technical details of the architecture and the
python API for modules are described.

.. toctree::
   :maxdepth: 3

   architecture
   protocol
   http
   core_api
   module_api
   packaging

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

