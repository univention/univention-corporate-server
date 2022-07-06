.. _chap-ucr:

**************************
Univention Config Registry
**************************
.. index::
   single: config registry
   see: UCR; config registry
   see: registry; config registry

The |UCSUCR| (UCR) is a local mechanism, which is used on all UCS system roles
to consistently configure all services and applications. It consists of a
database, were the currently configured values are stored, and a mechanism to
trigger certain actions, when values are changed. This is mostly used to create
configuration files from templates by filling in the configured values. In
addition to using simple place holders its also possible to use Python code for
more advanced templates or to call external programs when values are changed.
UCR values can also be configured through an UDM policy in Univention directory
service (LDAP), which allows values to be set consistently for multiple hosts of
a domain.

.. toctree::

   usage
   configuration
   templates
   integration
   examples
   python3
