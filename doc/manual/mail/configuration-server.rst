.. _mail-serverconfig-general:

Configuration of the mail server
================================

.. _mail-serverconfig-relay:

Configuration of a relay host for sending the emails
----------------------------------------------------

By default Postfix creates a direct SMTP connection to the mail server
responsible for the domain when an email is sent to a non-local address. This
server is determined by querying the MX record in the DNS.

Alternatively, a mail relay server can also be used, i.e., a server which
receives the mails and takes over their further sending. This type of mail relay
server can be provided by a superordinate corporate headquarters or the nternet
provider, for example. To set a relay host, it must be entered as a fully
qualified domain name (FQDN) in the |UCSUCRV| :envvar:`mail/relayhost`.

If authentication is necessary on the relay host for sending, the |UCSUCRV|
:envvar:`mail/relayauth` must be set to ``yes`` and the
:file:`/etc/postfix/smtp_auth` file edited. The relay host, username and
password must be saved in this file in one line: :samp:`{FQDN-Relayhost}
{username}:{password}`


To adopt the changes in Postfix, complete the step with the command:

.. code-block:: console

   $ postmap /etc/postfix/smtp_auth


.. note::

   To ensure an encrypted connection while using a relay host, the Postfix
   option ``smtp_tls_security_level=encrypt`` has to be set. |UCSUCS| will set
   this option automatically, if :envvar:`mail/relayhost` is set and
   :envvar:`mail/relayauth` is set to ``yes`` and
   :envvar:`mail/postfix/tls/client/level` is not set to ``none``.

.. _mail-serverconfig-mailsize:

Configuration of the maximum mail size
--------------------------------------

The |UCSUCRV| :envvar:`mail/messagesizelimit` can be used to set the maximum
size in bytes for incoming and outgoing emails. Postfix must be restarted after
modifying the setting. The preset maximum size is ``10240000`` bytes. If the value
is configured to ``0`` the limit is effectively removed. Please note that email
attachments are enlarged by approximately a third due to the *base64* encoding.

.. _mail-serverconfig-archivefolder:

Configuration of a blind carbon copy for mail archiving solutions
-----------------------------------------------------------------

If the |UCSUCRV| :envvar:`mail/archivefolder` is set to an email address,
Postfix sends a blind carbon copy of all incoming and outgoing emails to this
address. This results in an archiving of all emails. The email address must
already exist. It can be either one already registered in |UCSUCS| as the email
address of a user, or an email account with an external email service. As
standard the variable is not set.

Postfix must then be restarted.

.. _mail-serverconfig-softbounce:

Configuration of soft bounces
-----------------------------

In a number of error situations (e.g., for non-existent users) the result may be
a mail bounce, i.e., the email cannot be delivered and is returned to the sender.
When |UCSUCRV| :envvar:`mail/postfix/softbounce` is set to ``yes`` emails are
never returned after a bounce, but instead are held in the queue. This setting
is particularly useful during configuration work on the mail server.

.. _mail-serverconfig-smtp-ports:

Configuration of SMTP ports
---------------------------

On a |UCSUCS| mail server Postfix is configured to listen for connections on
three ports:

Port 25 - SMTP
   Port 25 (``SMTP``) should be used by other mail servers only. By default
   authentication is disabled. If submission of emails from users is wanted on
   port 25, authentication can be enabled by setting the |UCSUCRV|
   :envvar:`mail/postfix/mastercf/options/smtp/smtpd_sasl_auth_enable` to
   ``yes``.

Port 465 - SMTPS
   Port 465 (``SMTPS``) allows authentication and email submission through a SSL
   encrypted connection. ``SMTPS`` has been declared deprecated in favor of port
   587 but is kept enabled for legacy clients.

Port 587 - Submission
   Port 587 (``Submission``) allows authentication and email submission through
   a TLS encrypted connection. The use of ``STARTTLS`` is enforced.

The submission port should be preferred by email clients. The use of the ports
``25`` and ``465`` for email submission is deprecated.

.. _mail-serverconfig-postscreen:

Configuration of additional checks
----------------------------------

When using a mail server that is directly accessible from the internet, there is
always a risk that spam sender, spam bots or broken mail servers are continually
trying to deliver unwanted emails (for example spam) to the UCS system.

To reduce the load of the mail server for such cases, Postfix brings its own
service with the name :program:`postscreen`, which is put in front of Postfix
and accepts incoming SMTP connections. On these incoming SMTP connections, some
lightweight tests are first performed. If the result is positive, the respective
connection is passed on to Postfix. Otherwise the SMTP connection is terminated
and thus the incoming mail is rejected before being in the area of
responsibility of the UCS mail server.

By default, :program:`postscreen` is not active. By setting the |UCSUCRV|
:envvar:`mail/postfix/postscreen/enabled` to the value ``yes``,
:program:`postscreen` can be activated.

Various UCR variables with the prefix :envvar:`mail/postfix/postscreen/` can be
used to configure :program:`postscreen`. A list of all relevant UCR variables
including descriptions can be retrieved e.g. on command line via the command:

.. code-block:: console

   $ ucr search --verbose mail/postfix/postscreen/

.. note::

   After each change of a UCR variable for :program:`postscreen` the
   configuration of Postfix and :program:`postscreen` should be reloaded. This
   can be triggered e.g. via the command :command:`systemctl reload postfix`.

.. _mail-serverconfig-maincflocal:

Custom Postfix configuration
----------------------------

It is possible to modify the Postfix configuration, that resides within the file
:file:`/etc/postfix/main.cf`, beyond the variables that can be set with
|UCSUCRV|.

If the file :file:`/etc/postfix/main.cf.local` exists, its content will be
appended to the file :file:`main.cf`. To transfer changes of
:file:`main.cf.local` to :file:`main.cf`, the following command must be
executed:

.. code-block:: console

   $ ucr commit /etc/postfix/main.cf


For the Postfix service to accept the changes, it must be reloaded:

.. code-block:: console

   $ systemctl reload postfix


If a Postfix variable that has previously been set in :file:`main.cf` is set
again in :file:`main.cf.local`, Postfix will issue a warning to the log file
:file:`/var/log/mail.log`.

.. note::

   If Postfix' behavior is not as expected, first remove configuration settings
   made by :file:`main.cf.local`. Rename the file or comment out its content.
   Next run the two commands above. The configuration will then return to UCS
   defaults.

.. _mail-serverconfig-alias-expansion-limit:

Configuring the alias expansion limit
-------------------------------------

When sending a mail to a group including other nested groups, the mail may not
be accepted/delivered. This is caused by Postfix trying to expand the number of
the primary recipients via *virtual alias expansion*. This number is limited to
``1000`` users by default which might be too low.

To adjust the number to (for instance) 5000 users, the following line can be
added or edited in :file:`/etc/postfix/main.cf.local`:

.. code-block::

   virtual_alias_expansion_limit = 5000

Afterwards Postfix needs to be restarted:

.. code-block:: console

   $ systemctl restart postfix

.. _mail-renamed-users:

Handling of mailboxes during email changes and the deletion of user accounts
-----------------------------------------------------------------------------

A user's mailbox is linked to the primary email address and not to the
username. The |UCSUCRV| :envvar:`mail/dovecot/mailbox/rename` can be used to
configure the reaction when the primary email address is changed:

* If the variable is set to ``yes``, the name of the user's IMAP mailbox is
  changed. This is the standard setting since UCS 3.0.

* If the setting is ``no``, it will not be possible to read previous emails
  any more once the user's primary email address is changed! If another user is
  assigned a previously used primary email address, they receive access to the
  old IMAP structure of this mailbox.

The |UCSUCRV| :envvar:`mail/dovecot/mailbox/delete` can be used to configure,
whether the IMAP mailbox is also deleted. The value ``yes`` activates the
removal of the corresponding IMAP mailbox if one of the following actions is
performed:

* deletion of the user account

* removal of the primary email address from the user account

* changing the user's mail home server to a different system

With default settings (``no``) the mailboxes are kept if one of the actions
above is performed.

The combination of the two variables creates four possible outcomes when the
email address is changed:

.. list-table:: Renaming of email addresses
   :header-rows: 1
   :widths: 4 8

   * - mail/dovecot/mailbox/…
     - Meaning

   * - ``rename=yes`` and ``delete=no`` (default)
     - The existing mailbox will be renamed. Emails will be preserved and will
       be accessible at the new address.

   * - ``rename=yes`` and ``delete=yes``
     - The existing mailbox will be renamed. Emails will be preserved and will
       be accessible at the new address.

   * - ``rename=no`` and ``delete=no``
     - A new, empty mailbox will be created. The old one will be preserved on
       disk with the old name and will thus not be accessible to users.

   * - ``rename=no`` and ``delete=yes``
     - A new, empty mailbox will be created. The old one will be deleted from
       the hard disk.

.. _mail-homeserver:

Distribution of an installation on several mail servers
-------------------------------------------------------

The UCS mail system offers the possibility of distributing users across several
mail servers. To this end, each user is assigned a so-called mail home server on
which the user's mail data are stored. When delivering an email, the
responsible home server is automatically determined from the LDAP directory.

It must be observed that global IMAP folders (see
:ref:`mail-management-shared-folder`) are assigned to a mail home server.

If the mail home server changes for a user, the user's mail data is *not* moved
to the server automatically.

.. _mail-serverconfig-nfs:

Mail storage on NFS
-------------------

Dovecot supports storing emails and index files on cluster file systems and on
NFS. Some settings are necessary to prevent data loss in certain situations.

The following settings assume that mailboxes are not accessed simultaneously by
multiple servers. This is the case if for each user exactly one mail home server
has been configured.

* :envvar:`mail/dovecot/process/mmap_disable`\ ``=yes``

* :envvar:`mail/dovecot/process/dotlock_use_excl`\ ``=yes``

* :envvar:`mail/dovecot/process/mail_fsync`\ ``=always``

To achieve higher performance, index files can be kept on the local servers
disk, instead of storing them together with the messages on NFS. The index
files can then be found at :file:`/var/lib/dovecot/index/`. To activate this
option, set |UCSUCRV| :envvar:`mail/dovecot/location/separate_index`\ ``=yes``.

With the above settings the mail server should work without problems on NFS.
There are however a lot of different client and server systems in service. In
case you encounter problems, here are some notes that might help:

* If NFSv2 is in use (not the case if the NFS server is a |UCSUCS|), please set
  :envvar:`mail/dovecot/process/dotlock_use_excl`\ ``=no``.

* If *lockd* is not in use (not the case on |UCSUCS| systems) or if even with
  *lockd* in use locking error are encountered, set
  :envvar:`mail/dovecot/process/lock_method`\ ``=dotlock``. This does lower the
  performance, but solves most locking related errors.

* Dovecot flushes NFS caches when needed if you set
  :envvar:`mail/dovecot/process/mail_nfs_storage`\ ``=yes``, but unfortunately
  this doesn't work 100%, so you can get random errors. The same holds for
  flushing NFS caches after writing index files with
  :envvar:`mail/dovecot/process/mail_nfs_index`\ ``= yes``.

The Dovecot documentation has more information on the topic: `Dovecot Wiki: NFS
<https://wiki2.dovecot.org/NFS>`_.

.. _mail-serverconfig-limits:

Connection limits
-----------------

In a default |UCSUCS| configuration Dovecot allows ``400`` concurrent IMAP and POP3
connections each. That is enough to serve at least 100 concurrently logged in
IMAP users, possibly a lot more.

How many IMAP connections are opened by a user depends on the clients they use:

* Webmail opens just a few short lived connections.

* Desktop clients keep multiple connections open over a long period of time.

* Mobile clients keep just a few connections open over a long period of time.
  But they tend to never close them, unnecessarily wasting resources.

The limits exist mainly to resist denial of service attacks that open a lot of
connections and create lots of processes.

To list the open connections, run:

.. code-block:: console

   $ doveadm who

To display the total amount of open connections, run:

.. code-block:: console

   $ doveadm who -1 | wc -l

The |UCSUCRV|\ s :envvar:`mail/dovecot/limits`\ ``/*`` can be set to modify the
limits. The process of adapting those variables is only semi automatic, because
of their complex interaction. For the meaning of each variable refer to `Dovecot
Wiki: Service configuration <https://wiki2.dovecot.org/Services>`_.

Dovecot uses separate processes for login and to access emails. The limits for
these can be configured separately. The maximum number of concurrent connections
to a service and the maximum number of processes for a service is also
configured separately. Setting
``mail/dovecot/limits/default_client_limit = 3000`` changes the limit
for the maximum number of concurrent connections to the IMAP and POP3 services
but does not change the maximum number of processes allowed to run. With the
|UCSUCS| default settings Dovecot runs in "High-security mode": each connection
is served by a separate process. The default is to allow only ``400`` processes, so
only 400 connections can be made.

To allow 3000 clients to connect to their emails, another |UCSUCRV| has to be
set:

.. code-block:: console

   $ ucr set mail/dovecot/limits/default_client_limit=3000
   $ ucr set mail/dovecot/limits/default_process_limit=3000
   $ doveadm reload


Reading :file:`/var/log/dovecot.info` reveals a warning:

::

   config: Warning: service auth { client_limit=2000 } is lower than required under max. load (15000)
   config: Warning: service anvil { client_limit=1603 } is lower than required under max. load (12003)

The services ``auth`` (responsible for login and SSL connections) and ``anvil``
(responsible for statistics collection) are set to their default limits.
Although 3000 POP3 and IMAP connections and processes are allowed, the
connection limit for the login service is too low. Leaving it like this will
lead to failed logins.

The values are so high, because ``default_client_limit`` and
``default_process_limit`` do not only lift limits for IMAP and POP3, but also
for other services like ``lmtp`` and ``managesieve-login``. Those services can
now start more processes that have to be monitored and can theoretically make
more authentication requests. This increases the number of possible concurrent
connections to the ``auth`` and ``anvil`` services.

The values have to be adapted, using the numbers from the log file:

.. code-block:: console

   $ ucr set mail/dovecot/limits/auth/client_limit=15000
   $ ucr set mail/dovecot/limits/anvil/client_limit=12003
   $ doveadm reload

Another warning appears in
:file:`/var/log/dovecot.info`:

::

   master: Warning: fd limit (ulimit -n) is lower than required under max. load (2000 < 15000),…
    because of service auth { client_limit }

The Linux kernel controlled setting ``ulimit`` setting (limit on the number of
files/connections a process is allowed to open) is changed only when the Dovecot
service is restarted:

.. code-block:: console

   $ systemctl restart dovecot

No more warnings are written to the log file and both IMAP and POP3 servers now
accept 3000 client connections each.

|UCSUCS| configures Dovecot to run in "High-security mode" by default. For
installations with 10.000s of users, Dovecot offers the "High-performance mode".
The performance guide has further details on how to configure it, see `UCS
performance guide
<https://docs.software-univention.de/performance-guide-5.0.html>`_.
