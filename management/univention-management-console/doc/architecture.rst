============
Architecture
============

The Univention Management Console service consists of a four
components. The communication between these components is encrypted
using SSL. The following image shows the architecture and the
communication channels.

.. image:: umc-architecture.png

* The *UMC server* is the core component. It provides access to the
  modules and manages the connection and verifies that only authorized
  users gets access. The protocol used to communicate is the Univention
  Management Console Protocol (UMCP) in version 2.0

* The *UMC HTTP server* ss a small web server that provides HTTP
  access to the UMC server. It is used by the web frontend.

* The *UMC module* processes are forked by the UMC server to provide
  a specific area of management tasks wthin a session.

--------------------
Asynchrone Framework
--------------------

All server-side components of the UMC service are based on the
asynchrone framework Python Notifier, that provides techniques for
handling quasi parallel tasks based on events. The framework follows
three basic concepts:

* *Non-blocking sockets* For servers that should handling several
  communication channels at a time have to use so called non-blocking
  sokets. This is an option that needs to be set for each socket, that
  should be management by the server. This is necessary to avoid
  blocking on read or write operations on he sockets.

* *Timer* To perform tasks after a defined amount of time the
  framework provides an API to manage timer (one shot or periodically).

* *Signals* To inform components within a process of a specific a
  events the framework provide the possiblity to define
  signals. Components being interested in events may place a
  registration.

Further details, examples and a complete API documentation for Python
Notifier can be found at the website of the project
`Python Notifier website <http://blog.bitkipper.net/?page_id=51>`_.
