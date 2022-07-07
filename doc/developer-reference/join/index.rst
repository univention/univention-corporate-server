.. _chap-join:

***********
Domain join
***********

.. index::
   single: domain join
   see: join; domain join

A UCS system is normally joined into a domain. This establishes a trust relation
between the different hosts, which enables users to access services provided by
any host of the domain.

Joining a system into a domain requires write permission to create and modify
entries in the Univention directory service (LDAP). Local ``root`` permission on
the joining host is not sufficient to get write access to the domain wide LDAP
service. Instead valid LDAP credentials must be entered interactively by the
administrator doing the join.

.. toctree::

   scripts
   status
   run
   write-join
   write-unjoin
