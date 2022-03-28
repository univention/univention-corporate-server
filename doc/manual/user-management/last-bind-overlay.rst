.. _users-lastbind-overlay-module:

Overlay module for recording an account's last successful LDAP bind
===================================================================

.. caution::

   Before using this feature please read :uv:kb:`support article about
   activating the OpenLDAP lastbind overlay module <14404>`.

The optional `lastbind overlay module
<http://manpages.ubuntu.com/manpages/xenial/man5/slapo-lastbind.5.html>`_ for
OpenLDAP allows recording the timestamp of the last successful LDAP bind in the
``authTimestamp`` attribute and can for example be used to detect unused
accounts.

The ``lastbind`` overlay module can be activated by setting the |UCSUCRV|
:envvar:`ldap/overlay/lastbind` to ``yes`` and restarting the OpenLDAP server.
When the module is activated on an UCS server, a timestamp is written to the
account's ``authTimestamp`` attribute when that account logs into the LDAP
server. The |UCSUCRV| :envvar:`ldap/overlay/lastbind/precision` can be used to
configure the time in seconds that has to pass before the ``authTimestamp``
attribute is updated. This prevents a large number of write operations that can
impair performance.

The ``authTimestamp`` attribute can only be queried on the LDAP server where the
``lastbind`` overlay module is activated. It is not replicated to other LDAP
servers. For that reason the
:file:`/usr/share/univention-ldap/univention_lastbind.py` script can be executed
to collect the youngest ``authTimestamp`` value from all reachable LDAP servers
in the UCS domain and save it into the ``lastbind`` extended UDM attribute of a
user. The script can be invoked to update the ``lastbind`` extended attribute of
one or all users. The ``lastbind`` extended attribute maps to the
``univentionAuthTimestamp`` LDAP attribute.

One way to keep the ``lastbind`` extended attribute
up-to-date is by creating a cron job via UCR:

.. code-block:: console

   $ ucr set cron/update_lastbind_attribute/command='\
   > /usr/share/univention-ldap/univention_lastbind.py \
   > --allusers' \
   > cron/update_lastbind_attribute/time='00 06 * * *'  # daily at 06:00 a.m.


More information on how to set cron jobs via UCR can be found in
:ref:`computers-Defining-cron-jobs-in-Univention-Configuration-Registry`.
