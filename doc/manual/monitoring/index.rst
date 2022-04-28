.. _monitoring-general:

*************************
Infrastructure monitoring
*************************

UCS offers two different solutions for infrastructure monitoring.

On the one hand the UCS Dashboard helps administrators to quickly read the state
of domains and individual servers. On the other hand, under UCS 4.4, with Nagios
it is possible to continuously check computers and services in the background
and proactively trigger a notification if a warning level is reached.

With UCS 5.0 support for the Nagios server component has been discontinued, but
the systems can still be monitored, e.g. by UCS 4.4 Nagios servers, as described
in the UCS 4.4 manual.

.. toctree::
   :caption: Chapter contents:

   dashboard
   nagios
