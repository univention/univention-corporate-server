.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _listener-handler-low:

Low-level Listener module
=========================

Each Listener module is implemented as a plain Python module. The required
variables and functions must be declared at the module level.

.. code:: python

   description : str = "Module description"
   filter : str = "(objectClass=*)"
   attributes : List[str] = ["objectClass"]
   modrdn : str = "1"


On top of the description in :ref:`listener-handler` the following extra notes apply:

.. py:currentmodule:: low_level

.. py:data:: filter
   :type: str

   (required)

   .. note::

      The name :py:data:`filter` has the drawback that it shadows the Python built-in
      function :external+python:py:func:`filter`, but its use has historical reasons. If
      that function is required for implementing the listener module, an
      alias-reference may be defined before overwriting the name or it may be
      explicitly accessed through the Python ``__builtin__`` module.

In addition to the static strings, a module must implement several functions.
They are called in different situations of the lifecycle of the module.

.. code:: python

   def initialize() -> None:
     pass
   def handler(
     dn: str,
     new: Dict[str, List[bytes]],
     old: Dict[str, List[bytes]],
     command: str = '',
   ) -> None:
     pass
   def clean() -> None:
     pass
   def prerun() -> None:
     pass
   def postrun() -> None:
     pass
   def setdata(key: str, value: str) -> None:
     pass

.. py:function:: handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], command: str = '')

   :param str dn:
   :param Dict[str, List[bytes]] new:
   :param Dict[str, List[bytes]] old:
   :param str command:

   :rtype: None

   (required)

   This function is called for each change matching the ``filter`` and
   ``attributes`` as declared in the header of the module. The distinguished
   name (dn) of the object is supplied as the first argument ``dn``.

   Depending on the type of modification, ``old`` and ``new`` may each
   independently either be ``None`` or reference a Python dictionary of lists.
   Each list represents one of the multi-valued attributes of the object. The
   |UCSUDL| uses a local cache to store the values of each object as it has seen
   most recently. This cache is used to supply the values for ``old``, while the
   values in ``new`` are those retrieved from that LDAP directory service which
   is running on the same server as the |UCSUDN| (|UCSPRIMARYDN| or
   |UCSBACKUPDN| servers in the domain).

   If and only if the global ``modrdn`` setting is enabled, ``command``
   is passed as a fourth argument. It contains a single letter, which
   indicates the original type of modification. This can be used to
   further distinguish an modrdn operation from a delete operation
   followed by a create operation.

   ``m`` (modify)
      Signals a modify operation, where an existing object is changed. ``old``
      contains a copy of the previously values from the listener cache. ``new``
      contains the current values as retrieved from the leading LDAP directory
      service.

   ``a`` (add)
      Signals the addition of a new object. ``old`` is ``None`` and ``new``
      contains the latest values of the added object.

   ``d`` (delete)
      Signals the removal of a previously existing object. ``old`` contains a
      copy of the previously cached values, while ``new`` is ``None``.

   ``r`` (rename: modification of distinguished name through ``modrdn``)
      Signals a change in the distinguished name, which may be caused by
      renaming the object or moving the object from one container into another.
      The module is called with this command instead of the *delete* command, so
      that modules can recognize this special case and avoid deletion of local
      data associated with the object. The module will be called again with the
      *add* command just after the *modrdn* command, where it should process the
      rename or move operation. Each module is responsible for keeping track of
      the rename-case by internally storing the previous distinguished name
      during the *modrdn* phase of this two phased operation.

   ``n`` (new or schema change)
      This command can signal two changes:

      * If ``dn`` is ``cn=Subschema``, it signals that a schema change occurred.

      * All other cases signal the creation of a new intermediate object, which
        should be handled just like a normal :py:func:`add` operation. This
        happens when an object is moved into a new container, which does not yet
        exists in the local LDAP service.

   .. important::

      The listener only retrieves the latest state and passes it to this
      function. Due to stopped processes or due to network issues this
      can lead to multiple changes being aggregated into the first
      change. This may cause ``command`` to no longer match the values
      supplied through ``new``. For example, if the object has been
      deleted in the meantime, the function is called once with
      ``new=None`` and ``command='m'``. This can also lead to the
      function being called multiple times with ``old`` being equal to
      ``new``.

.. py:function:: setdata(key: str, value: str)

   :param str key:
   :param str value:

   :rtype: None

   (optional)

   This function is called up to four times by the |UCSUDL| main process to pass
   configuration data into the modules. The following ``key``\ s are supplied in
   the following order:

   ``basedn``
      The base distinguished name the |UCSUDL| is using.

   ``binddn``
      The distinguished name the |UCSUDL| is using to authenticate to the LDAP
      server (through ``simple bind``).

   ``bindpw``
      The password the |UCSUDL| is using to authenticate to the LDAP
      server.

   ``ldapserver``
      The hostname of the LDAP server the |UCSUDL| is currently reading
      from.

   .. note::

      It's strongly recommended to avoid initiating LDAP modifications
      from a listener module. This potentially creates a complex
      modification dynamic, considering that a module may run on several
      systems in parallel at their own timing.
