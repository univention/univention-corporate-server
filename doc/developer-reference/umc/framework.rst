.. _umc-framework:

Asynchronous framework
======================

All server-side components of the UMC service are based on the asynchronous
framework Python Notifier, that provides techniques for handling quasi parallel
tasks based on events. The framework follows three basic concepts:

Non-blocking sockets
   For servers that should handling several communication channels at a time
   have to use so called non-blocking sockets. This is an option that needs to
   be set for each socket, that should be management by the server. This is
   necessary to avoid blocking on read or write operations on the sockets.

Timer
   To perform tasks after a defined amount of time the framework provides an API
   to manage timer (one shot or periodically).

Signals
   To inform components within a process of a specific a events the framework
   provide the possibility to define signals. Components being interested in
   events may place a registration.

Further details, examples and a complete API documentation for Python Notifier
can be found at the `website of Python Notifier <univention-py-notifier_>`_.
