.. _listener-details:

Technical Details
=================

.. index::
   single: directory listener; debug

.. _listener-details-credentials:

User-ID and Credentials
-----------------------

.. index::
   single: directory listener; credentials

The listener runs with the effective permissions of the user ``listener``. If
``root``-privileges are required, :py:func:`listener.SetUID` can be used as a
context manager or method wrapper to switch the effective *UID*.

.. code:: python

   from listener import SetUID

   @SetUID()
   def prerun() -> None:
               pass

   def postrun() -> None:
       with SetUID(0):
               pass


.. _listener-details-cache:

Internal Cache
--------------------------------------

.. index::
   single: directory listener; cache

The directory :file:`/var/lib/univention-directory-listener/` contains several
files:

:file:`cache/cache.mdb`, :file:`cache/lock.mdb`
   Starting with UCS 4.2, the LMDB cache database contains a copy of all objects
   and their attributes. It is used to supply the old values supplied through
   the ``old`` parameter, when the function :py:func:`handler` is called.

   The cache is also used to keep track, for which object which module was
   called. This is required when a new module is added, which is invoked for all
   already existing objects when the |UCSUDL| is restarted.

   On domain controllers the cache could be replaced by doing a query to
   the local LDAP server, before the new values are written into it. But
   |UCSMANAGEDNODE| doesn't have a local LDAP server, so there the cache is
   needed. Also note that the cache keeps track of the associated listener
   modules, which is not available from the LDAP.

   It also contains the :uv:kb:`CacheMasterEntry <13149>`, which stores the
   notifier and schema ID.

:file:`cache.lock`
   Starting with UCS 4.2, this file is used to detect if a listener opened the
   cache database.

:file:`cache.db`, :file:`cache.db.lock`
   Before UCS 4.2, the BDB cache file contained a copy of all objects and their
   attributes. With the update to UCS 4.2, it gets converted into an LMDB
   database.

:file:`notifier_id`
   This legacy file contains the last notifier ID read from the |UCSUDN|.

:file:`handlers/`
   For each module the directory contains a text file consisting of a single
   number. The name of the file is derived from the values of the variable
   ``name`` as defined in each listener module. The number is to be interpreted
   as a bit-field of ``HANDLER_INITIALIZED=0x1`` and ``HANDLER_READY=0x2``. If
   both bits are set, it indicates that the module was successfully initialized
   by running the function :py:func:`initialize() <your_module.initialize>`.
   Otherwise both bits are unset.

The package :program:`univention-directory-listener` contains
several commands useful for controlling and debugging problems with the
|UCSUDL|. This can be useful for debugging listener cache inconsistencies.

.. _listener-commands-ctrl:

:command:`univention-directory-listener-ctrl`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The command :command:`univention-directory-listener-ctrl status` shows the
status of the Listener. This includes the transaction from the |UCSPRIMARYDN| in
comparison to the last processes transaction. It also shows a list of all
installed modules and their status.

The command :command:`univention-directory-listener-ctrl resync $name` can be
used to reset and re-initialize a module. It stops any currently running
listener process, removes the state file for the specified module and starts the
listener process again. This forces the functions :py:func:`clean()
<your_module.clean>` and :py:func:`initialize() <your_module.initialize>` to be
called one after the other.

.. _listener-commands-dump:

:command:`univention-directory-listener-dump`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The command :command:`univention-directory-listener-dump` can
be used to dump the cache file
:file:`/var/lib/univention-directory-listener/cache.db`.
The |UCSUDL| must be stopped first by invoking :command:`systemctl stop
univention-directory-listener`. It outputs the cache in format
compatible to the LDAP Data Interchange Format (LDIF).

.. _listener-commands-verify:

:command:`univention-directory-listener-verify`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: directory listener; verify

The command :command:`univention-directory-listener-verify` can be used to
compare the content of the cache file
:file:`/var/lib/univention-directory-listener/cache.db` to the content of an
LDAP server. The |UCSUDL| must be stopped first by invoking :command:`systemctl
stop univention-directory-listener`. LDAP credentials must be supplied at the
command line. For example, the following command would use the machine password:

.. code-block:: console

   $ univention-directory-listener-verify \
     -b "$(ucr get ldap/base)" \
     -D "$(ucr get ldap/hostdn)" \
     -w "$(cat /etc/machine.secret)"


.. _listener-commands-getnid:

:command:`get_notifier_id.py`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   single: directory listener; notifier ID

The command
:command:`/usr/share/univention-directory-listener/get_notifier_id.py` can be
used to get the latest ID from the notifier. This is done by querying the
|UCSUDN| running on the LDAP server configured through the |UCSUCRV|
:envvar:`ldap/master`. The returned value should be equal to the value currently
stored in the file :file:`/var/lib/univention-directory-listener/notifier_id`.
Otherwise, the |UCSUDL| might still be processing a transaction or it might
indicate a problem with the |UCSUDL|

.. _listener-details-internal:

Internal working
----------------

The Listener/Notifier mechanism is used to trigger arbitrary actions when
changes occur in the LDAP directory service. In addition to the LDAP server
:command:`slapd` it consists of two other services: The |UCSUDN| service runs
next to the LDAP server and broadcasts change information to interested parties.
The |UCSUDL| service listens for those notifications, downloads the changes and
runs listener modules performing arbitrary local actions like storing the data
in a local LDAP server for replication or generating configuration files for
non-LDAP-aware local services.

.. _listener-schema:

.. figure:: /images/ListenerNotifier.png
   :alt: Listener/Notifier mechanism

   Listener/Notifier mechanism

On startup the listener connects to the notifier and opens a persistent TCP
connection to port ``6669``. The host can be configured through several |UCSUCRV|\ s:

* If :envvar:`notifier/server` is explicitly set, only that named host is used.
  In addition, the |UCSUCRV| :envvar:`notifier/server/port` can be used to
  explicitly configure a different TCP port other then ``6669``.

* Otherwise, on the |UCSPRIMARYDN| and on all |UCSBACKUPDN|\ s, only the host
  named in :envvar:`ldap/master` is used.

* Otherwise, on all other system roles a host is chosen randomly from the
  combined list of names in :envvar:`ldap/master` and :envvar:`ldap/backup`.

  This list of |UCSBACKUPDN|\ s stored in the |UCSUCRV| :envvar:`ldap/backup` is
  automatically updated by the listener module :file:`ldap_server.py`.

The following steps occur on changes:

.. _listener-procedure:

#. An LDAP object is modified on the |UCSPRIMARYDN|. Changes initiated on all
   other system roles are re-directed to the |UCSPRIMARYDN|.

#. The UCS-specific overlay-module :program:`translog` assigns the next
   transaction number. It uses the file :file:`/var/lib/univention-ldap/last_id`
   to keep track of the last transaction number.

   As a fallback the transaction number of the last entry from the file
   :file:`/var/lib/univention-ldap/listener/listener` or
   :file:`/var/lib/univention-ldap/notify/transaction` is used. The module
   appends the transaction ID, DN and change type to the file
   :file:`/var/lib/univention-ldap/listener/listener`.

   Referred to as ``FILE_NAME_LISTENER``, ``TRANSACTION_FILE`` in the source
   code.

#. The |UCSUDN| watches that file and waits until it becomes non empty. The file
   is then renamed to :file:`/var/lib/univention-ldap/listener/listener.priv`
   (referred to as ``FILE_NAME_NOTIFIER_PRIV``) and the original files is
   re-created empty. The transactions from the renamed file are processed
   line-by-line and are appended to the file
   :file:`/var/lib/univention-ldap/notify/transaction` (referred to as
   ``FILE_NAME_TF`` in the source code), including the DN. Since protocol
   version 3 the notifier also stores the same information within the LDAP
   server by creating the entry :samp:`reqSession={ID},cn=translog`. After
   successful processing the renamed file is deleted. For efficient access by
   transaction ID the index :file:`transaction.index` is updated.

#. All listeners get notified of the new transaction. Before
   :uv:erratum:`4.3x427` the information already included the latest transaction
   ID, DN and the change type. With protocol version 3 only the transaction ID
   is included.

#. Each listener opens a connection to the LDAP server running on the UCS system
   which was used to query the Notifier. With protocol version 3 the listener
   first queries the LDAP server for the missing DN and change type information
   by retrieving the entry :samp:`reqSession={ID},cn=translog`. With that it
   retrieves the latest state of the object identified through the DN. If access
   is blocked, for example, by selective replication, the change is handled as a
   delete operation instead.

#. The old state of the object is fetched from the local
   :ref:`listener-details-cache` located in
   :file:`/var/lib/univention-directory-listener/cache/`.

#. For each module it is checked, if either the old or new state of the object
   matches the ``filter`` and ``attributes`` specified in the corresponding
   Python variables. If not, the module is skipped. By default
   :file:`replication.py` is always called first to guarantee that the data is
   available from the local LDAP server for all subsequent modules. Since
   :uv:erratum:`5.0x164` the order of how modules are called can be configured
   using the per module property :py:data:`priority <your_module.priority>`.

#. If the function :py:func:`prerun() <your_module.prerun>` of module was not
   called yet, this is done to signal the start of changes.

#. The function :py:func:`handler() <low_level.handler>` specified in the module
   is called, passing in the DN and the old and new state.

#. The main listener process updates its cache with the new values, including
   the names of the modules which successfully handled that object. This
   guarantees that the module is still called, even when the filter criteria
   would no longer match the object after modification.

#. On a |UCSBACKUPDN| the |UCSUDL| writes the transaction data to the file
   :file:`/var/lib/univention-ldap/listener/listener` (referred to as
   ``FILE_NAME_LISTENER``, ``TRANSACTION_FILE`` in the source code) to allow the
   |UCSUDN| to be cascaded. This is configured internally with the option ``-o``
   of :command:`univention-directory-listener` and is done for load balancing
   and failover reasons.

#. The transaction ID is written into the legacy local file
   :file:`/var/lib/univention-directory-listener/notifier_id`. It also is
   written into the *master record* of the listener cache.

After 15 seconds of inactivity the function :py:func:`postrun()
<your_module.postrun>` is invoked for all prepared modules. This signals a break
in the stream of changes and requests the module to release its resources and/or
start pending operations.

.. _listener-details-schema:

LDAP Schema handling
--------------------

.. index::
   single: LDAP; schema
   single: listener; schema replication

The LDAP Schema is managed on the |UCSPRIMARYDN|. Extensions must be made
available there first. All other systems running LDAP replica download it from
there using the |UCSUDN| / |UCSUDL| mechanism.

#. On the |UCSPRIMARYDN| the LDAP Schema is extracted by the script
   :file:`/etc/init.d/slapd` on each start. The MD5 hash is stored in
   :file:`/var/lib/univention-ldap/schema/md5`.

#. On each change the counter in file
   :file:`/var/lib/univention-ldap/schema/id/id` is incremented.

#. |UCSUDN| monitors that file and makes the value available over the network.
   It can be queried by running
   :command:`/usr/share/univention-directory-listener/get_notifier_id.py -s`.

#. |UCSUDL| retrieves the value during each transaction. It is stored in the
   local file :file:`/var/lib/univention-ldap/schema/id/id` and in the
   ``CacheMasterEntry`` of the :ref:`listener-details-cache`.

#. On change the Listener downloads the current Schema from the LDAP server of
   the |UCSPRIMARYDN|, saves it to the local schema file
   :file:`/var/lib/univention-ldap/schema.conf` and restarts the local service
   ``slapd``.

#. The Listener then continues processing transactions.

.. _listener-python-migration:

Python 3 migration
------------------

.. index::
   single: Python 3; migration

Since UCS 5.0 the |UCSUDL| uses Python 3 to execute listener modules.

For a successful migration all functions must be migrated to work with Python 3.
There is no change in the module variables (``name``, ``description``,
``filter``, ...) necessary.

The data structure of the arguments ``new`` and ``old`` given to the
:py:func:`handler() <low_level.handler>` function now explicitly differentiates
between byte strings (:py:class:`bytes`) and unicode strings (:py:class:`str`).
The dictionary keys are strings while the LDAP attribute values are list of byte
strings:

.. code:: python

   {
     'associatedDomain': [b'example.net'],
     'krb5RealmName': [b'EXAMPLE.NET'],
     'dc': [b'example'],
     'nisDomain': [b'example.net'],
     'objectClass': [
       b'top',
       b'krb5Realm',
       b'univentionPolicyReference',
       b'nisDomainObject',
       b'domainRelatedObject',
       b'domain',
       b'univentionBase',
       b'univentionObject'
     ],
     'univentionObjectType': [b'container/dc'],
   }


While in UCS 4 :py:func:`handler() <low_level.handler>` typically looked like:

.. code:: python

   def handler(
       dn:  # type: str,
       new,  # type: Dict[str, List[str]]
       old,  # type: Dict[str, List[str]]
   ):  # type: (...) -> None
       if new and 'myObjectClass' in new.get('objectClass', []):
           value = new['myAttribute'][0]
           ...


In UCS 5 it would look like:

.. code:: python

   def handler(
       dn: str,
       new: Dict[str, List[bytes]],
       old: Dict[str, List[bytes]],
   ) -> None:
       if new and b'myObjectClass' in new.get('objectClass', []):
           value = new['myAttribute'][0].decode('UTF-8')
           ...
