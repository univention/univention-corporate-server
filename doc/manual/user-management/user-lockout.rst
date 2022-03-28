.. _users-faillog:

Automatic lockout of users after failed login attempts
======================================================

By default, a user can enter their password incorrectly any number of
times. To hinder brute force attacks on passwords, an automatic lockout
for user accounts can be activated after a configured number of failed
login attempts.

UCS unifies various methods for user authentication and authorization.
Depending on the installed software components, there may be different
mechanisms for configuring and counting failed login attempts.

The three different methods are described in the next sections.

.. _users-faillog-samba:

Samba Active Directory Service
------------------------------

In Samba Active Directory environments, various services are provided by
Samba, such as Kerberos. To lockout users after too many failed login
attempts, the tool :command:`samba-tool` can be used.


* To show the currently configured values:

  .. code-block::

     $ samba-tool domain passwordsettings show

* To specify how often a user can attempt to log in with an incorrect password
  before the account is locked:

  .. code-block::

     $ samba-tool domain passwordsettings set --account-lockout-threshold=5

* To specify the number of minutes an account will be locked after too many
  incorrect passwords have been entered:

  .. code-block::

     $ samba-tool domain passwordsettings set --account-lockout-duration=3

* To define the number of minutes after which the counter is reset:

  .. code-block::

     samba-tool domain passwordsettings set --reset-account-lockout-after=5

  If an account gets automatically unlocked after the lockout duration, the
  counter is not reset immediately, to keep the account under strict monitoring
  for some time. During the time window between the end of the lockout duration
  and the point when the counter gets reset, a single attempt to log in with an
  incorrect password will lock the account immediately again.


The manual unlocking of a user is done in the user administration on the tab
:guilabel:`Account` by activating the checkbox *Unlock account*.

.. _users-faillog-pam:

PAM-Stack
---------

The automatic locking of users after failed logins in the PAM stack can be
enabled by setting the |UCSUCRV| :envvar:`auth/faillog` to ``yes``. The upper
limit of failed login attempts at which an account lockout is configured in the
|UCSUCRV| :envvar:`auth/faillog/limit`. The counter is reset each time the
password is entered correctly.

The lockout is activated locally per system by default. In other words, if a
user enters their password incorrectly too many times on one system, they can still
login on another system. Setting the |UCSUCRV|
:envvar:`auth/faillog/lock_global` will make the lock effective globally and
register it in the LDAP directory. The global lock can only be set on
|UCSPRIMARYDN|/Backup systems as other system roles do not have the necessary
permissions in the LDAP directory. On all systems with any of these system
roles, the lockout gets automatically activated locally or deactivated again via
the listener module, depending on the current lock state in the LDAP directory.

As standard, the lockout is not subject to time limitations and must be reset by
the administrator. However, it can also be reset automatically after a certain
time interval has elapsed. This is done by specifying a time period in seconds
in the |UCSUCRV| :envvar:`auth/faillog/unlock_time`. If the value is set to 0,
the lock is reset immediately.

By default, the ``root`` user is excluded from the password lock, but can also
be subjected to it by setting the |UCSUCRV| :envvar:`auth/faillog/root` to
``yes``.

If accounts are only locked locally, the administrator can unlock a user account
by entering the command:

.. code-block::

   $ faillog -r -u USERNAME

If the lock occurs globally in the LDAP directory, the user can be reset in the
|UCSUMC| module :guilabel:`Users` on the tab *Account* via the checkbox *Unlock
account*.

.. _users-faillog-openldap:

OpenLDAP
--------

On UCS Directory Nodes, automatic account locking can be enabled for too many
failed LDAP server login attempts. The MDB LDAP backend must be used. This is
the default backend since UCS 4, previous systems must be migrated to the MDB
LDAP backend, see `UCS performance guide
<https://docs.software-univention.de/performance-guide-5.0.html>`_.

Automatic account locking must be enabled for each UCS Directory Node.
To do this, the |UCSUCRV|\ s :envvar:`ldap/ppolicy` and
:envvar:`ldap/ppolicy/enabled` must be set to
``yes`` and the OpenLDAP server must be restarted:

.. code-block:: console

   $ ucr set ldap/ppolicy=yes ldap/ppolicy/enabled=yes
   $ systemctl restart slapd


The default policy is designed so that five repeated failed LDAP server login
attempts within five minutes cause the lockout. A locked account can only be
unlocked by a domain administrator through the UMC module :guilabel:`Users` via
the checkbox *Unlock account* on the *Account* tab.

The number of repeated failed LDAP server login attempts can be adjusted
in the configuration object with the *objectClass* ``pwdPolicy``:

.. code-block:: console

   $ univention-ldapsearch objectclass=pwdPolicy


``pwdMaxFailure``
   attribute determines the number of LDAP authentication errors before locking.

``pwdMaxFailureCountInterval``
   attribute determines the time interval in seconds that is considered. Failed
   login attempts outside this interval are ignored in the count.

The following command can be used to block the account after 10
attempts:

.. code-block:: console

   $ LB="$(ucr get ldap/base)"
   $ ldapmodify -x -D "cn=admin,$LB" -y /etc/ldap.secret <<__EOT__
   > dn: cn=default,cn=ppolicy,cn=univention,$LB
   > changetype: modify
   > replace: pwdMaxFailure
   > pwdMaxFailure: 10
   > __EOT__


The manual unlocking of a user is done in the user administration on the tab
*Account* by activating the checkbox *Unlock account*.
