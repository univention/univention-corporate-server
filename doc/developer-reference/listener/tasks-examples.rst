.. _listener-example:

Listener tasks and examples
===========================

.. index::
   single: directory listener; example module

All changes trigger a call to the function :py:func:`handler`. For simplicity and
readability it is advisable to delegate the different change types to different
sub-functions.

.. _listener-example-api:

Listener API example
--------------------

The following boilerplate code uses the newer listener API.

Source code:
:uv:src:`management/univention-directory-listener/examples/listener_module_template.py`

.. code:: python

   # -*- coding: utf-8 -*-
   #
   # Copyright 2017-2022 Univention GmbH
   #
   # https://www.univention.de/
   #
   # All rights reserved.
   #
   # The source code of this program is made available
   # under the terms of the GNU Affero General Public License version 3
   # (GNU AGPL V3) as published by the Free Software Foundation.
   #
   # Binary versions of this program provided by Univention to you as
   # well as other copyrighted, protected or trademarked materials like
   # Logos, graphics, fonts, specific documentations and configurations,
   # cryptographic keys etc. are subject to a license agreement between
   # you and Univention.
   #
   # This program is provided in the hope that it will be useful,
   # but WITHOUT ANY WARRANTY; without even the implied warranty of
   # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   # GNU Affero General Public License for more details.
   #
   # You should have received a copy of the GNU Affero General Public
   # License with the Debian GNU/Linux or Univention distribution in file
   # /usr/share/common-licenses/AGPL-3; if not, see
   # <https://www.gnu.org/licenses/>.

   from __future__ import absolute_import

   from typing import Dict, Optional, List

   from univention.listener import ListenerModuleHandler


   class ListenerModuleTemplate(ListenerModuleHandler):

       class Configuration(object):
           name = 'unique_name'
           description = 'listener module description'
           ldap_filter = '(&(objectClass=inetOrgPerson)(uid=example))'
           attributes = ['sn', 'givenName']

       def create(self, dn: str, new: Dict[str, List[bytes]]) -> None:
           self.logger.debug('dn: %r', dn)

       def modify(
           self,
           dn: str,
           old: Dict[str, List[bytes]],
           new: Dict[str, List[bytes]],
           old_dn: Optional[str],
       ) -> None:
           self.logger.debug('dn: %r', dn)
           if old_dn:
               self.logger.debug('it is (also) a move! old_dn: %r', old_dn)
           self.logger.debug('changed attributes: %r', self.diff(old, new))

       def remove(self, dn: str, old: Dict[str, List[bytes]]) -> None:
           self.logger.debug('dn: %r', dn)

.. _listener-example-simple:

Basic example
-------------

The following boilerplate code delegates each change type to a separate
function. It does not handle renames and moves explicitly, but only as
the removal of the object at the old dn and the following addition at
the new dn.

Source code:
:uv:src:`doc/developer-reference/listener/simple.py`

.. code:: python

   from typing import Dict, List


   def handler(
       dn: str,
       new: Dict[str, List[bytes]],
       old: Dict[str, List[bytes]],
   ) -> None:
       if new and not old:
           handler_add(dn, new)
       elif new and old:
           handler_modify(dn, old, new)
       elif not new and old:
           handler_remove(dn, old)
       else:
           pass  # ignore


   def handler_add(dn: str, new: Dict[str, List[bytes]]) -> None:
       """Handle addition of object."""
       pass  # replace this


   def handler_modify(
       dn: str,
       old: Dict[str, List[bytes]],
       new: Dict[str, List[bytes]],
   ) -> None:
       """Handle modification of object."""
       pass  # replace this


   def handler_remove(dn: str, old: Dict[str, List[bytes]]) -> None:
       """Handle removal of object."""
       pass  # replace this

.. _listener-example-modrdn:

Rename and move
---------------

.. index::
   single: directory listener; modrdn

In case rename and move actions should be handled separately, the following code
may be used:

Source code:
:uv:src:`doc/developer-reference/listener/modrdn.py`

.. code:: python

   from typing import Dict, List

   modrdn = "1"

   _delay = None


   def handler(
       dn: str,
       new: Dict[str, List[bytes]],
       old: Dict[str, List[bytes]],
       command: str = "",
   ) -> None:
       global _delay
       if _delay:
           old_dn, old = _delay
           _delay = None
           if "a" == command and old['entryUUID'] == new['entryUUID']:
               handler_move(old_dn, old, dn, new)
               return
           handler_remove(old_dn, old)

       if "n" == command and "cn=Subschema" == dn:
           handler_schema(old, new)
       elif new and not old:
           handler_add(dn, new)
       elif new and old:
           handler_modify(dn, old, new)
       elif not new and old:
           if "r" == command:
               _delay = (dn, old)
           else:
               handler_remove(dn, old)
       else:
           pass  # ignore, reserved for future use


   def handler_add(dn: str, new: Dict[str, List[bytes]]) -> None:
       """Handle creation of object."""
       pass  # replace this


   def handler_modify(
       dn: str,
       old: Dict[str, List[bytes]],
       new: Dict[str, List[bytes]],
   ) -> None:
       """Handle modification of object."""
       pass  # replace this


   def handler_remove(dn: str, old: Dict[str, List[bytes]]) -> None:
       """Handle removal of object."""
       pass  # replace this


   def handler_move(
       old_dn: str,
       old: Dict[str, List[bytes]],
       new_dn: str,
       new: Dict[str, List[bytes]],
   ) -> None:
       """Handle rename or move of object."""
       pass  # replace this


   def handler_schema(
       old: Dict[str, List[bytes]],
       new: Dict[str, List[bytes]],
   ) -> None:
       """Handle change in LDAP schema."""
       pass  # replace this

.. warning::

   Please be aware that tracking the two subsequent calls for ``modrdn`` in
   memory might cause duplicates, in case the |UCSUDL| is terminated while such
   an operation is performed. If this is critical, the state should be stored
   persistently into a temporary file.

.. _listener-example-user:

Full example with packaging
---------------------------

The following example shows a listener module, which logs all changes to users
into the file :file:`/root/UserList.txt`.

Source code:
:uv:src:`doc/developer-reference/listener/printusers/`

.. code:: python

   """
   Example for a listener module, which logs changes to users.
   """

   from __future__ import print_function

   import errno
   import os
   from collections import namedtuple
   from typing import Dict, List

   import univention.debug as ud
   from listener import SetUID

   name = 'printusers'
   description = 'print all names/users/uidNumbers into a file'
   filter = ''.join("""\
   (&
       (|
           (&
               (objectClass=posixAccount)
               (objectClass=shadowAccount)
           )
           (objectClass=univentionMail)
           (objectClass=sambaSamAccount)
           (objectClass=simpleSecurityObject)
           (objectClass=inetOrgPerson)
       )
       (!(objectClass=univentionHost))
       (!(uidNumber=0))
       (!(uid=*$))
   )""".split())
   attributes = ['uid', 'uidNumber', 'cn']
   _Rec = namedtuple('_Rec', 'uid uidNumber cn')

   USER_LIST = '/root/UserList.txt'


   def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
       """
       Write all changes into a text file.
       This function is called on each change.
       """
       if new and old:
           _handle_change(dn, new, old)
       elif new and not old:
           _handle_add(dn, new)
       elif old and not new:
           _handle_remove(dn, old)


   def _handle_change(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
       """
       Called when an object is modified.
       """
       o_rec = _rec(old)
       n_rec = _rec(new)
       ud.debug(ud.LISTENER, ud.INFO, 'Edited user "%s"' % (o_rec.uid,))
       _writeit(o_rec, u'edited. Is now:')
       _writeit(n_rec, u'')


   def _handle_add(dn: str, new: Dict[str, List[bytes]]) -> None:
       """
       Called when an object is newly created.
       """
       n_rec = _rec(new)
       ud.debug(ud.LISTENER, ud.INFO, 'Added user "%s"' % (n_rec.uid,))
       _writeit(n_rec, u'added')


   def _handle_remove(dn: str, old: Dict[str, List[bytes]]) -> None:
       """
       Called when an previously existing object is removed.
       """
       o_rec = _rec(old)
       ud.debug(ud.LISTENER, ud.INFO, 'Removed user "%s"' % (o_rec.uid,))
       _writeit(o_rec, u'removed')


   def _rec(data):
       # type (Dict[str, List[str]]) -> _Rec
       """
       Retrieve symbolic, numeric ID and name from user data.
       """
       return _Rec(*(data.get(attr, (None,))[0] for attr in attributes))


   def _writeit(rec, comment):
       # type: (_Rec, str) -> None
       """
       Append CommonName, symbolic and numeric User-IDentifier, and comment to file.
       """
       nuid = u'*****' if rec.uid in ('root', 'spam') else rec.uidNumber
       indent = '\t' if comment is None else ''
       try:
           with SetUID():
               with open(USER_LIST, 'a') as out:
                   print(u'%sName: "%s"' % (indent, rec.cn), file=out)
                   print(u'%sUser: "%s"' % (indent, rec.uid), file=out)
                   print(u'%sUID: "%s"' % (indent, nuid), file=out)
                   if comment:
                       print(u'%s%s' % (indent, comment,), file=out)
       except IOError as ex:
           ud.debug(
               ud.LISTENER, ud.ERROR,
               'Failed to write "%s": %s' % (USER_LIST, ex))


   def initialize():
       # type: () -> None
       """
       Remove the log file.
       This function is called when the module is forcefully reset.
       """
       try:
           with SetUID():
               os.remove(USER_LIST)
           ud.debug(
               ud.LISTENER, ud.INFO,
               'Successfully deleted "%s"' % (USER_LIST,))
       except OSError as ex:
           if errno.ENOENT == ex.errno:
               ud.debug(
                   ud.LISTENER, ud.INFO,
                   'File "%s" does not exist, will be created' % (USER_LIST,))
           else:
               ud.debug(
                   ud.LISTENER, ud.WARN,
                   'Failed to delete file "%s": %s' % (USER_LIST, ex))

Some comments on the code:

* The LDAP filter is specifically chosen to only match user objects, but not
  computer objects, which have a ``uid`` characteristically terminated by a
  ``$``-sign.

* The ``attribute`` filter further restricts the module to only trigger on
  changes to the numeric and symbolic user identifier and the last name of the
  user.

* To test this run a command like :command:`tail -f /root/UserList.txt &`. Then
  create a new user or modify the *lastname* of an existing one to trigger the
  module.

For packaging the following files are required:

:file:`debian/printusers.install`
   The module should be installed into the directory
   :file:`/usr/lib/univention-directory-listener/system/`.

   .. code-block:: console

      $ printusers.py usr/lib/univention-directory-listener/system/

:file:`debian/printusers.postinst`
   The |UCSUDL| must be restarted after package installation and removal:

   .. code-block:: bash

      #! /bin/sh
      set -e

      case "$1" in
      configure)
          systemctl restart univention-directory-listener
          ;;
      abort-upgrade|abort-remove|abort-deconfigure)
          ;;
      *)
          echo "postinst called with unknown argument \`$1'" >&2
          exit 1
          ;;
      esac

      #DEBHELPER#

      exit 0

:file:`debian/printusers.postrm`

   .. code-block:: bash

      #! /bin/sh
      set -e

      case "$1" in
      remove)
          systemctl restart univention-directory-listener
          ;;
      purge|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)
          ;;
      *)
          echo "postrm called with unknown argument \`$1'" >&2
          exit 1
          ;;
      esac

      #DEBHELPER#

      exit 0

.. _listener-example-setdata:

A little bit more object oriented
---------------------------------

For larger modules it might be preferable to use a more object oriented design
like the following example, which logs referential integrity violations into a
file.

Source code: :uv:src:`doc/developer-reference/listener/obj.py`

.. code:: python

   from __future__ import absolute_import, print_function

   import os
   from pwd import getpwnam
   from typing import Dict, List, Optional, Tuple

   import ldap
   import univention.debug as ud
   from listener import SetUID

   name = "refcheck"
   description = "Check referential integrity of uniqueMember relations"
   filter = "(uniqueMember=*)"
   attribute = ["uniqueMember"]
   modrdn = "1"


   class LocalLdap(object):
       PORT = 7636

       def __init__(self) -> None:
           self.data: Dict[str, str] = {}
           self.con: Optional[ldap.ldapobject.LDAPObject] = None

       def setdata(self, key: str, value: str):
           self.data[key] = value

       def prerun(self) -> None:
           try:
               self.con = ldap.initialize('ldaps://%s:%d' % (self.data["ldapserver"], self.PORT))
               self.con.simple_bind_s(self.data["binddn"], self.data["bindpw"])
           except ldap.LDAPError as ex:
               ud.debug(ud.LISTENER, ud.ERROR, str(ex))

       def postrun(self) -> None:
           if not self.con:
               return
           try:
               self.con.unbind()
               self.con = None
           except ldap.LDAPError as ex:
               ud.debug(ud.LISTENER, ud.ERROR, str(ex))


   class LocalFile(object):
       USER = "listener"
       LOG = "/var/log/univention/refcheck.log"

       def initialize(self) -> None:
           try:
               ent = getpwnam(self.USER)
               with SetUID():
                   with open(self.LOG, "w"):
                       pass
                   os.chown(self.LOG, ent.pw_uid, -1)
           except OSError as ex:
               ud.debug(ud.LISTENER, ud.ERROR, str(ex))

       def log(self, msg) -> None:
           with open(self.LOG, 'a') as log:
               print(msg, file=log)

       def clean(self) -> None:
           try:
               with SetUID():
                   os.remove(self.LOG)
           except OSError as ex:
               ud.debug(ud.LISTENER, ud.ERROR, str(ex))


   class ReferentialIntegrityCheck(LocalLdap, LocalFile):
       MESSAGES = {
           (False, False): "Still invalid: ",
           (False, True): "Now valid: ",
           (True, False): "Now invalid: ",
           (True, True): "Still valid: ",
       }

       def __init__(self) -> None:
           super(ReferentialIntegrityCheck, self).__init__()
           self._delay: Optional[Tuple[str, Dict[str, List[bytes]]]] = None

       def handler(
           self,
           dn: str,
           new: Dict[str, List[bytes]],
           old: Dict[str, List[bytes]],
           command: str = '',
       ) -> None:
           if self._delay:
               old_dn, old = self._delay
               self._delay = None
               if "a" == command and old['entryUUID'] == new['entryUUID']:
                   self.handler_move(old_dn, old, dn, new)
                   return
               self.handler_remove(old_dn, old)

           if "n" == command and "cn=Subschema" == dn:
               self.handler_schema(old, new)
           elif new and not old:
               self.handler_add(dn, new)
           elif new and old:
               self.handler_modify(dn, old, new)
           elif not new and old:
               if "r" == command:
                   self._delay = (dn, old)
               else:
                   self.handler_remove(dn, old)
           else:
               pass  # ignore, reserved for future use

       def handler_add(self, dn: str, new: Dict[str, List[bytes]]) -> None:
           if not self._validate(new):
               self.log("New invalid object: " + dn)

       def handler_modify(
           self,
           dn: str,
           old: Dict[str, List[bytes]],
           new: Dict[str, List[bytes]],
       ) -> None:
           valid = (self._validate(old), self._validate(new))
           msg = self.MESSAGES[valid]
           self.log(msg + dn)

       def handler_remove(self, dn: str, old: Dict[str, List[bytes]]) -> None:
           if not self._validate(old):
               self.log("Removed invalid: " + dn)

       def handler_move(
           self,
           old_dn: str,
           old: Dict[str, List[bytes]],
           new_dn: str,
           new: Dict[str, List[bytes]],
       ) -> None:
           valid = (self._validate(old), self._validate(new))
           msg = self.MESSAGES[valid]
           self.log("%s %s -> %s" % (msg, old_dn, new_dn))

       def handler_schema(
           self,
           old: Dict[str, List[bytes]],
           new: Dict[str, List[bytes]],
       ) -> None:
           self.log("Schema change")

       def _validate(self, data: Dict[str, List[bytes]]) -> bool:
           assert self.con
           try:
               for dn in data["uniqueMember"]:
                   self.con.search_ext_s(dn, ldap.SCOPE_BASE, attrlist=[], attrsonly=1)
               return True
           except ldap.NO_SUCH_OBJECT:
               return False
           except ldap.LDAPError as ex:
               ud.debug(ud.LISTENER, ud.ERROR, str(ex))
               return False


   _instance = ReferentialIntegrityCheck()
   initialize = _instance.initialize
   handler = _instance.handler
   clean = _instance.clean
   prerun = _instance.prerun
   postrun = _instance.postrun
   setdata = _instance.setdata
