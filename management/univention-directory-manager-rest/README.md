Architecture
============

The UDM REST API starts one gateway process and one subprocess for all possible languages.
All HTTP requests are forwarded to the language specific process by evaluating the `Accept-Language` header.
Each main process also starts another subprocess for sharing memory between those processes via a `multiprocessing.SyncManager`.

UDM currently translates strings at python import time which makes it impossible to use two languages in one process.

The gateway is defined in `src/univention/admin/rest/server/__init__.py`.
The server is defined in `src/univention/admin/rest/__main__.py`.
All HTTP resources are currently defined in `src/univention/admin/rest/module.py`.

CLI Client
==========
There is an unsupported CLI client and client library called `__udm` which tries to behave similar to the real `udm`.
It can be used to easy test basic operations.
A real supported client will follow in the Future™.
