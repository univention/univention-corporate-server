.. _computers-basic-system-services:

Basic system services
=====================

This chapter describes basic system services of a UCS Installation such
as the configuration of the PAM authentication framework, system logs
and the NSCD.

.. _computers-rootaccount:

Administrative access with the root account
-------------------------------------------

There is a ``root`` account on every UCS system for complete administrative
access. The password is set during installation of the system. The root user
**is not** stored in the LDAP directory, but instead in the local user accounts.

The password for the root user can be changed via the command line by using the
:command:`passwd` command. It must be pointed out that this process does not
include any checks regarding either the length of the password or the passwords
used in the past.

.. _computers-configuration-of-language-and-keyboard-settings:

Configuration of language and keyboard settings
-----------------------------------------------

In Linux, localization properties for software are defined in so-called
*locales*. Configuration includes, among other things, settings for date and
currency format, the set of characters in use and the language used for
internationalized programs. The installed locales can be changed in the UMC
module :guilabel:`Language settings` under :menuselection:`Language settings -->
Installed system locales`. The standard locale is set under *Default system
locale*.

.. _language-settings:

.. figure:: /images/computers_timezone.*
   :alt: Configuring the language settings

   Configuring the language settings

The *Keyboard layout* in the menu entry *Time zone and keyboard settings* is
applied during local logins to the system.

.. _computers-system-services:

Starting/stopping system services / configuration of automatic startup
----------------------------------------------------------------------

The UMC module :guilabel:`System services` can be used to check the current
status of a system service and to start or stop it as required.

.. _umc-services:

.. figure:: /images/umc-systemservices.*
   :alt: Overview of system services

   Overview of system services

In this list of all the services installed on the system, the current running
runtime status and a *Description* are displayed under *Status*. The service can
be started, stopped or restarted under :guilabel:`more`.

By default every service is started automatically when the system is started. In
some situations, it can be useful not to have the service start directly, but
instead only after further configuration. The action *Start manually* is used so
that the service is not started automatically when the system is started, but
can still be started subsequently. The action *Start never* also prevents
subsequent service starts.

.. _computers-authentication-pam:

Authentication / PAM
--------------------

Authentication services in Univention Corporate Server are realized via
*Pluggable Authentication Modules* (PAM). To this
end different login procedures are displayed on a common interface so
that a new login method does not require adaptation for existing
applications.

.. _computers-limiting-authentication-to-selected-users:

.. rubric:: Limiting authentication to selected users

By default only the ``root`` user and members of the ``Domain Admins`` group can
login remotely via SSH and locally on a ``tty``.

This restriction can be configured with the |UCSUCRV|
:samp:`auth/{SERVICE}/restrict`. Access to this service can be authorized by
setting the variables :samp:`auth/{SERVICE}/user/{USERNAME}` and
:samp:`auth/{SERVICE}/group/{GROUPNAME}` to ``yes``.

Login restrictions are supported for *SSH* (``sshd``), login on a *tty*
(``login``), *rlogin* (``rlogin``), *PPP* (``ppp``) and other services
(``other``). An example for *SSH*:

.. code-block::

   auth/sshd/group/Administrators: yes
   auth/sshd/group/Computers: yes
   auth/sshd/group/DC Backup Hosts: yes
   auth/sshd/group/DC Slave Hosts: yes
   auth/sshd/group/Domain Admins: yes
   auth/sshd/restrict: yes


.. _computers-configure-ldap-server:

Configuration of the LDAP server in use
---------------------------------------

Several LDAP servers can be operated in a UCS domain. The primary one used is
specified with the |UCSUCRV| :envvar:`ldap/server/name`, further servers can be
specified via the |UCSUCRV| :envvar:`ldap/server/addition`.

Alternatively, the LDAP servers can also be specified via a *LDAP server*
policy. The order of the servers determines the order of the computer's requests
to the server if a LDAP server cannot be reached.

By default only :envvar:`ldap/server/name` is set following the installation or
the domain join. If there is more than one LDAP server available, it is
advisable to assign at least two LDAP servers using the *LDAP server* policy in
order to improve redundancy. In cases of an environment distributed over
several locations, preference should be given to LDAP servers from the local
network.

.. _computers-configure-print-server:

Configuration of the print server in use
----------------------------------------

The print server to be used can be specified with the |UCSUCRV|
:envvar:`cups/server`.

Alternatively, the server can also be specified via the *Print server* policy in
the UMC module :guilabel:`Computers`.

.. _computers-logging-retrieval-of-system-messages-and-system-status:

Logging/retrieval of system messages and system status
------------------------------------------------------

.. _computers-log-files:

Log files
~~~~~~~~~

All UCS-specific log files (e.g., for the listener/notifier replication) are
stored in the :file:`/var/log/univention/` directory. Services write log messages their own
standard log files: for example, Apache to the file
:file:`/var/log/apache2/error.log`.

The log files are managed by :program:`logrotate`. It ensures that log files are
named in series in intervals (can be configured in weeks using the |UCSUCRV|
:envvar:`log/rotate/weeks`, with the default setting being 12) and older log
files are then deleted. For example, the current log file for the |UCSUDL| is
found in the :file:`listener.log` file; the one for the previous week in
:file:`listener.log.1`, etc.

Alternatively, log files can also be rotated only once they have reached a
certain size. For example, if they are only to be rotated once they reach a size
of 50 MB, the |UCSUCRV| :envvar:`logrotate/rotates` can be set to ``size 50M``.

The |UCSUCRV| :envvar:`logrotate/compress` is used to configure whether the
older log files are additionally zipped with :command:`gzip`.

.. _computers-logging-the-system-status:

Logging the system status
~~~~~~~~~~~~~~~~~~~~~~~~~

:command:`univention-system-stats` can be used to document the current system
status in the :file:`/var/log/univention/system-stats.log` file. The following
values are logged:

* The free disk space on the system partitions (:command:`df
  -lhT`)

* The current process list (:command:`ps auxf`)

* Two :command:`top` lists of the current processes and
  system load (:command:`top -b -n2`)

* The current free system memory (:command:`free`)

* The time elapsed since the system was started
  (:command:`uptime`)

* Temperature, fan and voltage indexes from
  :program:`lm-sensors`
  (:command:`sensors`)

* A list of the current Samba connections
  (:command:`smbstatus`)

The runtime in which the system status should be logged can be defined in Cron
syntax via the |UCSUCRV| :envvar:`system/stats/cron`, e.g., ``0,30 \* \* \* \*``
for logging every half and full hour. The logging is activated by setting the
|UCSUCRV| :envvar:`system/stats` to ``yes``. This is the default since UCS 3.0.

.. _computers-modules-top:

Process overview via |UCSUMC| module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UMC module :guilabel:`Process overview` displays a table of the current
processes on the system. The processes can be sorted based on the following
properties by clicking on the corresponding table header:

* CPU utilization in percent

* The username under which the process is running

* Memory consumption in percent

* The process ID

The menu item *more* can be used to terminate processes. Two different types of
termination are possible:

Terminate
   The action :guilabel:`Terminate` sends the process a ``SIGTERM`` signal; this
   is the standard method for the controlled termination of programs.

Force terminate
   Sometimes, it may be the case that a program - e.g., after crashing - can no
   longer be terminated with this procedure. In this case, the action
   :guilabel:`Force terminate` can be used to send the signal ``SIGKILL`` and
   force the process to terminate.

As a general rule, terminating the program with ``SIGTERM`` is preferable as
many programs then stop the program in a controlled manner and, for example,
save open files.

.. _computers-modules-diagnostic:

System diagnostic via |UCSUMC| module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The UMC module :guilabel:`System diagnostic` offers a corresponding user
interface to analyze a UCS system for a range of known problems.

The module evaluates a range of problem scenarios known to it and suggests
solutions if it is able to resolve the identified solutions automatically. This
function is displayed via ancillary buttons. In addition, links are shown to
further articles and corresponding UMC modules.

.. _computers-executing-recurring-actions-with-cron:

Executing recurring actions with Cron
-------------------------------------

Regularly recurring actions (e.g., the processing of log files) can be
started at a defined time with the Cron service. Such an action is known
as a cron job.

.. _computers-hourly-daily-weekly-monthly-execution-of-scripts:

Hourly/daily/weekly/monthly execution of scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Four directories are predefined on every UCS system, :file:`/etc/cron.hourly/`,
:file:`/etc/cron.daily/`, :file:`/etc/cron.weekly/` and
:file:`/etc/cron.monthly/`. Shell scripts which are placed in these directories
and marked as executable are run automatically every hour, day, week or month.

.. _cron-local:

Defining local cron jobs in :file:`/etc/cron.d/`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index:: cron; syntax
   :name: cron-syntax

A cron job is defined in a line, which is composed of a total of seven columns:

* Minute (0-59)

* Hour (0-23)

* Day (1-31)

* Month (1-12)

* Weekday (0-7) (0 and 7 both stand for Sunday)

* Name of user executing the job (e.g., root)

* The command to be run

The time specifications can be set in different ways. One can specify a specific
minute/hour/etc. or run an action every minute/hour/etc. with a ``*``. Intervals
can also be defined, for example ``*/2`` as a minute specification runs an
action every two minutes.

Example:

.. code-block::

   30 * * * * root /usr/sbin/jitter 600 /usr/share/univention-samba/slave-sync


.. _computers-defining-cron-jobs-in-univention-configuration-registry:

Defining cron jobs in Univention Configuration Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cron jobs can also be defined in |UCSUCR|. This is particularly useful if
they are set via a |UCSUDM| policy and are thus used on more than one
computer.

Each cron job is composed of at least two |UCSUCR| variables.
:samp:`{JOBNAME}` is a general description.

* :samp:`cron/{JOBNAME}/command` specifies the command to be run (required)

* :samp:`cron/{JOBNAME}/time` specifies the execution time (see
  :ref:`cron-local`) (required)

* As standard, the cron job is run as a user ``root``.
  :samp:`cron/{JOBNAME}/user` can be used to specify a different user.

* If an email address is specified under :samp:`cron/{JOBNAME}/mailto`, the
  output of the cron job is sent there per email.

* :samp:`cron/{JOBNAME}/description` can be used to provide a description.

.. _computers-nscd:

Name service cache daemon
-------------------------

Data of the NSS service is cached by the *Name Server Cache Daemon* (NSCD) in
order to speed up frequently recurring requests for unchanged data. Thus, if a
repeated request occurs, instead of a complete LDAP request to be processed, the
data are simply drawn directly from the cache.

Since UCS 3.1, the groups are no longer cached via the NSCD for performance and
stability reasons; instead they are now cached by a local group cache, see
:ref:`groups-cache`.

The central configuration file of the (:file:`/etc/nscd.conf`) is managed by
|UCSUCR|.

The access to the cache is handled via a hash table. The size of the hash table
can be specified in |UCSUCR|, and should be higher than the number of
simultaneously used users/hosts. For technical reasons, a prime number should be
used for the size of the table. The following table shows the standard values of
the variables:

.. list-table:: Default size of the hash table
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Default size of the hash table

   * - ``nscd /hosts/size``
     -  ``6007``

   * - ``nscd/passwd/size``
     - ``6007``

With very big caches it may be necessary to increase the size of the cache
database in the system memory. This can be configured through the |UCSUCR|
variables :envvar:`nscd/hosts/maxdbsize`, :envvar:`nscd/group/maxdbsize` and
:envvar:`nscd/passwd/maxdbsize`.

As standard, five threads are started by NSCD. In environments with many
accesses it may prove necessary to increase the number via the |UCSUCRV|
:envvar:`nscd/threads`.

In the basic setting, a resolved group or hostname is kept in cache for one
hour, a username for ten minutes. With the |UCSUCR| variables
:envvar:`nscd/group/positive_time_to_live` and
:envvar:`nscd/passwd/positive_time_to_live` these periods can be extended or
diminished (in seconds).

From time to time it might be necessary to manually invalidate the cache of the
NSCD. This can be done individually for each cache table with the following
commands:

.. code-block:: console

   $ nscd -i passwd
   $ nscd -i hosts


The verbosity of the log messages can be configured through the |UCSUCRV|
:envvar:`nscd/debug/level`.

.. _computers-ssh-login-to-systems:

SSH login to systems
--------------------

When installing a UCS system, an SSH server is also installed per preselection.
SSH is used for realizing encrypted connections to other hosts, wherein the
identity of a host can be assured via a check sum. Essential aspects of the SSH
server's configuration can be adjusted in |UCSUCR|.

By default the login of the privileged ``root`` user is permitted by SSH (e.g.
for configuring a newly installed system where no users have been created yet,
from a remote location).

* If the |UCSUCRV| :envvar:`sshd/permitroot` is set to ``without-password``,
  then no interactive password request will be performed for the ``root`` user,
  but only a login based on a public key. By this means brute force attacks to
  passwords can be avoided.

* To prohibit SSH login completely, this can be deactivated by setting the
  |UCSUCRV| :envvar:`auth/sshd/user/root` to ``no``.

The |UCSUCRV| :envvar:`sshd/xforwarding` can be used to configure
whether an X11 output should be passed on via SSH. This is necessary,
for example, for allowing a user to start a program with graphic output
on a remote computer by logging in with :command:`ssh -X
TARGETHOST`. Valid settings are ``yes`` and
``no``.

The standard port for SSH connections is port 22 via TCP. If a different
port is to be used, this can be arranged via the |UCSUCRV|
:envvar:`sshd/port`.

.. _basicservices-ntp:

Configuring the time zone / time synchronization
------------------------------------------------

The time zone in which a system is located can be changed in the UMC module
:guilabel:`Language settings` under :menuselection:`Time zone and keyboard
settings --> Time zone`.

Asynchronous system times between individual hosts of a domain can be the source
of a large number of errors, for example:

* The reliability of log files is impaired.

* Kerberos operation is disrupted.

* The correct evaluation of the validity periods of passwords can be disturbed

Usually the |UCSPRIMARYDN| functions as the time server of a domain. With the
|UCSUCR| variables :envvar:`timeserver`, :envvar:`timeserver2` and
:envvar:`timeserver3` external NTP servers can be included as time sources.

Manual time synchronization can be started by the command :command:`ntpdate`.

Windows clients joined in a Samba/AD domain only accept signed NTP time
requests. If the |UCSUCRV| :envvar:`ntp/signed` is set to ``yes``, the NTP
replies are signed by Samba/AD.
