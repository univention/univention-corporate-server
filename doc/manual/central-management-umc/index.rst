.. _central-general:

********
|UCSWEB|
********

.. highlight:: console

.. _fig-ucs-portal:

.. figure:: /images/portal.*
   :alt: UCS portal page

   UCS portal page

The |UCSWEB| is the central tool for managing a UCS domain as well as for
accessing installed applications of the domain.

The |UCSWEB| is divided into several subpages which all have a similarly
designed header. Via the symbols in the top right, one may launch a search on
the current page (magnifier) or open the user menu (three bars) (login is
possible through the latter). The login at the web interface is done via a
central page once for all sub pages of UCS as well as for third party
applications as far as a web based *single sign-on* is supported
(:ref:`central-management-umc-login`).

Central starting point for users and administrators for all following
actions is the UCS portal page (cf. :numref:`fig-ucs-portal`). By
default, the portal page is available on all system roles and allows an
overview of all Apps and further services which are installed in the UCS
domain. All aspects of the portal page can be customized to match one's
needs (:ref:`central-portal`).

For environments with more than one server, an additional entry to a
server overview page is shown on the portal page. This sub page gives an
overview of all available UCS systems in the domain. It allows a fast
navigation to other systems in order to adjust local settings via UMC
modules.

UMC modules are the web based tool for the administration of the UCS
domain. There are various modules available for the administration of
the different aspects of a domain depending on the respective system
role. Installing additional software components may add new UMC modules
to the system. :ref:`central-user-interface` describes
their general operation.

The subsequent sections detail the usage of various aspects of the domain
management. :ref:`central-navigation` gives an overview of the LDAP directory
browser. The use of administrative settings via policies is discussed in
:ref:`central-policies`. How to extend the scope of function of the domain
administration is detailed in :ref:`central-extended-attrs`.
:ref:`central-cn-and-ous` details how containers and organizational units can be
used to structure the LDAP directory. :ref:`delegated-administration` explains
delegating administration rights to additional user groups.

In conclusion, the command line interface of the domain administration is
illustrated (:ref:`central-udm`), and the evaluation of domain data via the UCS
reporting function are explained (:ref:`central-reports`).


.. toctree::
   :hidden:

   introduction
   login
   portal
   umc
   ldap-browser
   policies
   extended-attributes
   user-defined-ldap-structures
   delegated-administration
   udm-command
   http-api-domain-management
   directory-reports
   lets-encrypt
