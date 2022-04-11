************
|UCSUCRV|\ s
************

This appendix lists the |UCSUCRV|\ s mentioned in the document.

.. envvar:: auth/faillog

   Configures the automatic locking of users after failed login attempts in the
   PAM stack. To activate, set the value to ``yes``. For more information, see
   :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/limit

   Configures the upper limit of failed login attempts for a user account
   lockout. For more information, see :ref:`users-faillog-pam`.

.. envvar:: auth/faillog/lock_global

   Configure on |UCSPRIMARYDN| and |UCSBACKUPDN| to create a failed login
   account lockout globally and store it in the LDAP directory. For more
   information, see :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/root

   To make the user account ``root`` subject of the PAM stack account lockout,
   set the value to ``yes``. It defaults to ``no``. For more information, see
   :ref:`users-faillog-pam`.


.. envvar:: auth/faillog/unlock_time

   Configure a time interval to unlock an account lockout. The value is defined
   in seconds. The value ``0`` resets the lock immediately. For more
   information, see :ref:`users-faillog-pam`.


.. envvar:: auth/sshd/user/root

   To prohibit SSH login for the user ``root`` completely, set the value ``no``.
   For more information, see :ref:`computers-ssh-login-to-systems`.


.. envvar:: backup/clean/max_age

   Defines how long a UCS system keeps old backup files of the LDAP data.
   Allowed values are integer numbers and they define days. The system doesn't
   delete backup files when the variable is not set. See
   :ref:`domain-ldap-nightly-backup`.


.. envvar:: connector/ad/ldap/binddn

   Configures the LDAP DN of a priviledged replication user. For more
   information, see :ref:`ad-connector-ad-member-setup` and
   :ref:`ad-connector-ad-password`.


.. envvar:: connector/ad/ldap/bindpw

   Configures the password of a priviledged replication user. For more
   information, see :ref:`ad-connector-ad-member-setup` and
   :ref:`ad-connector-ad-password`.


.. envvar:: connector/ad/ldap/ssl

   To deactivate encrypted communication between the UCS system and Active
   Directory set the value to ``no``. For more information, see
   :ref:`ad-connector-ad-certificate`.


.. envvar:: connector/ad/mapping/group/language

   Configures the mapping for group name conversion in anglophone AD domains.
   For more information, see :ref:`ad-connector-groups`.


.. envvar:: connector/ad/mapping/user/ignorelist

   Configures a list of usernames that the AD Connector excludes from
   synchronization. For more information, see
   :ref:`ad-connector-details-on-preconfigured-synchronization`.


.. envvar:: connector/ad/poll/sleep

   Configures the interval to poll for changes in the AD domain. The default is
   ``5`` seconds. For more information, see :ref:`ad-connector-ad-connector-setup`.


.. envvar:: connector/ad/retryrejected

   Configures the number of cylces that the UCS AD Connector attempts to
   sychronize an object from the AD domain when it can't be synchronized. The
   default value is ``10`` cycles. For more information, see
   :ref:`ad-connector-ad-connector-setup`


.. envvar:: cups/cups-pdf/anonymous

   Configures the target directory for the *Generic CUPS-PDF Printer* for
   anonymous print jobs. It defaults to the value :file:`/var/spool/cups-pdf/`.
   For more information, see :ref:`pdf-printer`.


.. envvar:: cups/cups-pdf/cleanup/enabled

   To cleanup outdated print jobs of the *Generic CUPS-PDF Printer*, set the
   value to ``true``. For the storage time, see
   :envvar:`cups/cups-pdf/cleanup/keep`. For more information, see
   :ref:`pdf-printer`.


.. envvar:: cups/cups-pdf/cleanup/keep

   Configures the storage time in days for PDF files from the *Generic CUPS-PDF
   Printer*. For more information, see :ref:`pdf-printer`.


.. envvar:: cups/cups-pdf/directory

   Configures the target directory for the *Generic CUPS-PDF Printer*. It
   defaults to the value :file:`/var/spool/cups-pdf/%U` and uses a different
   directory for each user. For more information, see :ref:`pdf-printer`.

.. envvar:: cups/errorpolicy

   To automatically retry unsuccessful print jobs every 30 seconds, set the
   value to ``retry-job``. For more information, see
   :ref:`print-services-configuration`.


.. envvar:: cups/include/local

   To include configuration from :file:`/etc/cups/cupsd.local.conf`, set the
   value to ``true``. For more information, see
   :ref:`print-services-configuration`.


.. envvar:: cups/server

   Defines the print server to be used by a UCS system. For more information,
   see :ref:`computers-configureprintserver`.


.. envvar:: directory/manager/templates/alphanum/whitelist

   Define an allowlist of characters that are not removed by the ``:alphanum``
   option for the value definition in user templates. For more information, see
   :ref:`users-templates`.

.. envvar:: directory/manager/user_group/uniqueness

   Controls if UCS prevents users with the same username as existing groups. To
   deactivate the check for uniqueness, set the value to ``false``. For more
   information see :numref:`users-management-table-general-tab`.


.. envvar:: directory/manager/web/modules/computers/computer/wizard/disabled

   To disable the simplified wizard for computer management, set this variable
   to ``true``. For more information, see :ref:`computers-hostaccounts`.


.. envvar:: directory/manager/web/modules/groups/group/checks/circular_dependency

   Controls the check for circular dependencies regarding nested groups. To
   disable, set the value to ``no``. For more information, see
   :ref:`groups-nested`.


.. envvar:: directory/manager/web/modules/users/user/wizard/disabled

   Deactivates the simplified wizard to create users when the value is set to
   ``true``. In the default setting the wizard is activated. For more
   information see :ref:`users-management`.

.. envvar:: directory/reports/logo

   Defines the path and name to an image file for usage as logo in a Univention
   Directory report PDF file. For more information see
   :ref:`central-management-umc-adjustment-expansion-of-directory-reports`.


.. envvar:: dns/allow/transfer

   To deactivate the DNS zone transfer when using the OpenLDAP back end, set the
   value to ``none``. For more information, see
   :ref:`ip-config-configuration-of-zone-transfers`.


.. envvar:: dns/backend

   Configures the DNS backend. For more information, see
   :ref:`ip-config-dns-backend`.


.. envvar:: dns/debug/level

   Configures the debug level for BIND. For more information, see
   :ref:`ip-config-bind-debug`.


.. envvar:: dns/dlz/debug/level

   Configures the debug level for the Samba DNS backend. For more information,
   see :ref:`ip-config-bind-debug`.


.. envvar:: dns/forwarder1

   Defines the first *external DNS server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.


.. envvar:: dns/forwarder2

   Defines the second *external DNS server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.


.. envvar:: dns/forwarder3

   Defines the third *external DNS server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.

.. envvar:: freeradius/auth/helper/ntlm/debug

   Configures the debug level or verbosity for logging messages of FreeRADIUS.
   For more information, see :ref:`ip-config-radius-debugging`.


.. envvar:: gateway

   Configures the IPv4 network gateway. For more information, see
   :ref:`computers-ipv6`.


.. envvar:: google-apps/attributes/anonymize

   Configures the LDAP attributes of a user account that Google Apps for Work
   Connector synchronizes, but filles with random data. The value is a
   comma-separated list of LDAP attributes. For more information, see
   :ref:`idmcloud-gsuite-config`.


.. envvar:: google-apps/attributes/mapping/.*

   Defines a mapping of UCS LDAP attributes of a user account for
   synchronization to Google Apps attributes. The default settings usually
   suffice most environment needs. For more information, see
   :ref:`idmcloud-gsuite-config`.

.. envvar:: google-apps/attributes/never

   Configures the LDAP attributes of a user account that the Google Apps for
   Work Connector never synchronizes, even if mentioned in
   :envvar:`google-apps/attributes/mapping/.*` or
   :envvar:`google-apps/attributes/anonymize`. The value is a comma-separated
   list of LDAP attributes. For more information, see
   :ref:`idmcloud-gsuite-config`.


.. envvar:: google-apps/debug/werror

   Configure additional debug error for the Google Apps for Work. For more
   information, see :ref:`idmcloud-gsuite-debug`.


.. envvar:: google-apps/groups/sync

   Enables the synchronization of groups of the Google Apps for Work user groups
   with the value ``yes``. For more information, see
   :ref:`idmcloud-gsuite-config`.


.. envvar:: groups/default/domainadmins

   Configures the default group name for the domain administrator group. The
   value might be changed during an AD Takeover. For more information, see
   :ref:`windows-adtakeover-migrate`.


.. envvar:: grub/append

   Defines Linux kernel boot options that the GRUB boot loader passes to the
   Linux kernel for system boot. For more information, see :ref:`grub`.


.. envvar:: grub/bootsplash

   To deactivate the splash screen during system boot, set the value to
   ``nosplash``. For more information, see :ref:`grub`.


.. envvar:: grub/gfxmode

   Defines screen size and color depth for the GRUB boot menu. For more
   information, see :ref:`grub`.


.. envvar:: grub/timeout

   Defines the waiting period in seconds in the GRUB boot menu. During this
   waiting time alternative boot menu entries can be selected. The default value
   is ``5`` seconds. For more information, see :ref:`grub`.

.. envvar:: grub/xenhopt

   Defines options that are passed to the Xen hypervisor. For more information,
   see :ref:`grub`.


.. envvar:: interfaces/ethX/address

   Defines the network IPv4 address for the interface :samp:`eth{X}`. Replace
   :samp:`{X}` with the actual value for the interface. For more information,
   see :ref:`computers-ipv4`.


.. envvar:: interfaces/ethX/netmask

   Defines the network mask for the interface :samp:`eth{X}`. Replace
   :samp:`{X}` with the actual value for the interface. For more information,
   see :ref:`computers-ipv4`.


.. envvar:: interfaces/ethX/type

   Defines the network interface type for the interface :samp:`eth{X}`. Replace
   :samp:`{X}` with the actual value for the interface. For more information,
   see :ref:`computers-ipv4`.


.. envvar:: interfaces/ethX_Y/setting

   Defines an additional virtual interface. Replace :samp:`{X}` and
   :samp:`{Y}`with the actual value for the interface. For more information, see
   :ref:`computers-ipv4`.

.. envvar:: interfaces/ethX/ipv6/address

   Defines the network IPv6 address for the interface :samp:`eth{X}`. Replace
   :samp:`{X}` with the actual value for the interface. For more information,
   see :ref:`computers-ipv6`.


.. envvar:: interfaces/ethX/ipv6/prefix

   Defines the network IPv6 prefix for the interface :samp:`eth{X}`. Replace
   :samp:`{X}` with the actual value for the interface. For more information,
   see :ref:`computers-ipv6`.


.. envvar:: interfaces/ethX/ipv6/acceptRA

   Activates stateless address autoconfiguration (SLAAC) for the interface
   :samp:`eth{X}`. Replace :samp:`{X}` with the actual value for the interface.
   For more information, see :ref:`computers-ipv6`.


.. envvar:: ipv6/gateway

   Configures the IPv4 network gateway. For more information, see
   :ref:`computers-ipv6`.


.. envvar:: kerberos/adminserver

   Defines the system that provides the Kerberos admin server. See
   :ref:`domain-kerberos-admin-server`.


.. envvar:: kerberos/kdc

   Contains the reference to the KDC. Typically, a UCS system selects the KDC to
   be used from a DNS service record. With this variable administrators can
   configure an alternative KDC.

.. TODO Ask SME: What kind of value is expected?


.. envvar:: kerberos/realm

   Contains the name of the Kerberos realm. See :ref:`domain-kerberos`.

.. envvar:: kernel/blacklist

   Defines additional Linux kernel modules that need to be loaded during system
   boot. Single items must be separated with a semicolon (``;``). For more
   information, see :ref:`computers-hardware-drivers-kernel-modules`.


.. envvar:: kernel/modules

   Defines Linux kernel modules that must not be loaded during system
   boot. Single items must be separated with a semicolon (``;``). For more
   information, see :ref:`computers-hardware-drivers-kernel-modules`.


.. envvar:: ldap/acl/read/anonymous

   Controls if the LDAP server allows anonymous access to the LDAP directory.
   In the default configuration the LDAP server doesn't allow ananymous access
   to the LDAP directory.


.. envvar:: ldap/acl/read/ips

   A list of IP addresses for which the LDAP server allows anonymous access. See
   :ref:`domain-ldap-acls`.


.. envvar:: ldap/acl/nestedgroups

   Controls if nested groups are allowed. Per default nested groups are
   activated. See :ref:`domain-ldap-acls`.


.. envvar:: ldap/acl/user/passwordreset/accesslist/groups/dn

   Use a different group from the default ``User Password Admins`` group to
   reset user passwords. The value is a distinguished name (DN) to a user group.
   See :ref:`domain-ldap-delegation-of-the-priviledge-to-reset-user-passwords`.


.. envvar:: ldap/idletimeout

   Configures a time period in seconds after which the LDAP connection is cut
   off on the server side. See
   :ref:`domain-ldap-timeout-for-inactive-ldap-connections`.


.. envvar:: ldap/logging/exclude1

   Exclude individual areas of the directory service from logging. See
   :ref:`domain-ldap-directory-logger`.


.. envvar:: ldap/logging/excludeN

   See :envvar:`ldap/logging/exclude1`.


.. envvar:: ldap/logging/id-prefix

   Adds the transaction ID of an entry to the directory log. Possible values are
   the default ``yes`` and ``no``. See :ref:`domain-ldap-directory-logger`.

.. envvar:: ldap/master

   TBD

.. TODO : Define UCRV server/role

.. envvar:: ldap/overlay/lastbind

   To activate the ``lastbind`` overlay module for the LDAP server, set the
   value to ``yes``. For more information, see
   :ref:`users-lastbind-overlay-module`.

.. envvar:: ldap/overlay/lastbind/precision

   Configures the time in seconds that has to pass before the ``authTimestamp``
   is updated again by the ``lastbind`` overlay. For more information, see
   :ref:`users-lastbind-overlay-module`.


.. envvar:: ldap/overlay/memberof/memberof

   Configures the attribute at user objects that shows the group membership.
   Default value is ``memberOf``. For more information, see
   :ref:`groups-memberof`.


.. envvar:: ldap/policy/cron

   Time interval to write profile based UCR variables to a UCS system. The
   default value is one hour. For more information, see
   :ref:`ucr-templates-policy`.


.. envvar:: ldap/ppolicy

   To enable automatic account locking, set the value to ``yes``. Also set
   :envvar:`ldap/ppolicy/enabled`. For more information, see
   :ref:`users-faillog-openldap`.


.. envvar:: ldap/ppolicy/enabled

   To enable automatic account locking, set the value to ``yes``. Also set
   :envvar:`ldap/ppolicy`. For more information, see
   :ref:`users-faillog-openldap`.


.. envvar:: ldap/pw-bcrypt

   Activates :program:`bcrypt` as password hashing method when set to ``true``.
   See :ref:`domain-password-hashes`.


.. envvar:: ldap/server/addition

   Additional LDAP server a UCS system can query for information in the
   directory service.


.. envvar:: ldap/server/name

   The LDAP server the system queries for information in the directory service.


.. envvar:: listener/debug/level

   Defines the detail level for log messages of the listener to
   :file:`/var/log/univention/listener.log`. The possible values are from 0
   (only error messages) to 4 (all status messages). Once the debug level has
   been changed, the |UCSUDL| must be restarted.


.. envvar:: listener/shares/rename

   Contents of existing share directories are moved, when the path to a share is
   modified and the value is set to ``yes``. For more information, see
   :numref:`shares-management-general-tab-table` in
   :ref:`shares-management-general-tab`.


.. envvar:: local/repository

   Activates and deactivates the local repository. For more information see
   :ref:`software-createrepo`.

.. envvar:: logrotate/compress

   Controls, if rotated logfiles are zipped with :command:`gzip`. For more
   information, see :ref:`computers-log-files`.


.. envvar:: log/rotate/weeks

   Configures the logfile rotation interval on a UCS system in weeks. The
   default value is ``12`` weeks. For more information, see
   :ref:`computers-log-files`.


.. envvar:: logrotate/rotates

   Configures the logfile rotation according to the file size, for example
   ``size 50M``. For more information, see :ref:`computers-log-files`.


.. envvar:: machine/password/length

   Define the lenght for the computer password, also called *machin secret*.
   Default value is ``20``. For more information, see
   :ref:`computers-hostaccounts`.


.. envvar:: nameserver1

   Defines the first *Domain DNS Server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.


.. envvar:: nameserver2

   Defines the second *Domain DNS Server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.


.. envvar:: nameserver3

   Defines the third *Domain DNS Server*. For more information, see
   :ref:`computers-configuring-the-name-servers`.


.. envvar:: notifier/debug/level

   Defines the detail level for log messages of the notifier to
   :file:`/var/log/univention/notifier.log`. The possible values are from 0
   (only error messages) to 4 (all status messages). Once the debug level has
   been changed, the |UCSUDN| must be restarted.


.. envvar:: nscd/debug/level

   Defines the detail level for log messages of the NSCD. For more information,
   see :ref:`computers-nscd`.

.. envvar:: nscd/group/maxdbsize

   Configures the hash table size of the NSCD for groups. For more information,
   see :ref:`computers-nscd`.


.. envvar:: nscd/group/positive_time_to_live

   Configures the time that a resolved group or hostname is kept in the cache of
   NSCD. The default is one hour in seconds (``3600``). For more information,
   see :ref:`computers-nscd`.


.. envvar:: nscd/hosts/maxdbsize

   Configures the hash table size of the NSCD for hosts. The default value is
   ``6007``. For more information, see :ref:`computers-nscd`.


.. envvar:: nscd/passwd/maxdbsize

   Configures the hash table size of the NSCD for usernames. The default value
   is ``6007``. For more information, see :ref:`computers-nscd`.

.. envvar:: nscd/passwd/positive_time_to_live

   Configures the time that a resolved username is kept in the cache of
   NSCD. The default is ten minutes in seconds (``600``). For more information,
   see :ref:`computers-nscd`.


.. envvar:: nscd/threads

   Configures the number of threads that NSCD uses. Default value is ``5``. For
   more information, see :ref:`computers-nscd`.


.. envvar:: nss/group/cachefile/check_member

   When activated with ``true``, the cron job script for exporting the local
   group cache also checks, if the group members are still present in the LDAP
   directory. For more information, see :ref:`groups-cache`.


.. envvar:: nss/group/cachefile/invalidate_interval

   Defines the invalidation interval to control when the local group cache is
   considered invalid and a new export is run. For more information, see
   :ref:`groups-cache`.


.. envvar:: nss/group/cachefile/invalidate_on_changes

   Activates or deactivates the listener to invalidate the local group cache. To
   activate the listener, set the value to ``true``. Else, set it to ``false``.
   For more information, see :ref:`groups-cache`.


.. envvar:: nssldap/bindpolicy

   Controls the measures that the UCS system takes when the LDAP server cannot
   be reached. See :ref:`domain-ldap-name-service-switch-ldap-nss-module`.

.. TODO Ask SME: What is the default value and what values are possible?

.. envvar:: ntp/signed

   The NTP server replies with requests that are signed by Samba/AD when the
   value is set to ``yes``. For more information, see :ref:`basicservices-ntp`.


.. envvar:: office365/adconnection/wizard

   Defines the Azure AD connection alias that is used by the next run of the
   Microsoft 365 Configuration Wizard. For more information, see
   :ref:`idmcloud-o365-multipleconnections`.


.. envvar:: office365/attributes/anonymize

   Configures the LDAP attributes of a user account that the Microsoft 365
   connector synchronizes, but filles with random data. The value is a
   comma-separated list of LDAP attributes. For more information, see
   :ref:`idmcloud-o365-users`.


.. envvar:: office365/attributes/mapping/.*

   Defines a mapping of UCS LDAP attributes of a user account for
   synchronization to Azure attributes. The default settings usually suffice
   most environment needs. For more information, see :ref:`idmcloud-o365-users`.


.. envvar:: office365/attributes/never

   Configures the LDAP attributes of a user account that the Microsoft 365
   connector never synchronizes, even if mentioned in
   :envvar:`office365/attributes/sync` or
   :envvar:`office365/attributes/anonymize`. The value is a comma-separated list
   of LDAP attributes. For more information, see :ref:`idmcloud-o365-users`.


.. envvar:: office365/attributes/static/.*

   Configures LDAP attributes for synchronization with predefined values. For
   more information, see :ref:`idmcloud-o365-users`.


.. envvar:: office365/attributes/sync

   Configures the LDAP attributes of a user account that the Microsoft 365
   connector synchronizes. The value is a comma-separated list of LDAP
   attributes. For more information, see :ref:`idmcloud-o365-users`.


.. envvar:: office365/attributes/usageLocation

   Configures the default country for the user in Microsoft 365. Values are
   2-character abbreviations for countries. For more information, see
   :ref:`idmcloud-o365-users`.


.. envvar:: Office365/debug/werror

   Configure additional debug error for the Microsoft 365 connector. For more
   information, see :ref:`idmcloud-o365-debug`.

.. envvar:: office365/defaultalias

   Configures the default connection alias for Microsoft 365 enabled users and
   groups. For more information, see :ref:`idmcloud-o365-multipleconnections`.

.. envvar:: office365/groups/sync

   Enables the synchronization of groups of the Microsoft 365 users. To use
   teams, set the value to ``yes``. For more information, see
   :ref:`idmcloud-o365-teams`.


.. envvar:: password/hashing/bcrypt

   Activates :program:`bcrypt` as password hashing method when set to ``true``.
   See :ref:`domain-password-hashes`.


.. envvar:: password/hashing/bcrypt/cost_factor

   Defines the :program:`bcrypt` cost factor and defaults to ``12``. See
   :ref:`domain-password-hashes`.


.. envvar:: password/hashing/bcrypt/prefix

   Defines the :program:`bcrypt` prefix and defaults to ``2b``. See
   :ref:`domain-password-hashes`.


.. envvar:: password/hashing/method

   Defines the hashing method for the password hashes. The default is
   ``SHA-512``. See :ref:`domain-password-hashes`.


.. envvar:: password/quality/credit/digits

   Defines the minimum number of digits for a new password. For more
   information, see :ref:`users-passwords`. For more information, see
   :ref:`users-passwords`.


.. envvar:: password/quality/credit/lower

   Defines the minimum number of lowercase letters in the new password. For more
   information, see :ref:`users-passwords`.


.. envvar:: password/quality/credit/other

   Defines the minimum number of characters in the new password which are
   neither letters nor digits. For more information, see :ref:`users-passwords`.


.. envvar:: password/quality/credit/upper

   Defines the minimum number of uppercase letters in the new password. For more
   information, see :ref:`users-passwords`.


.. envvar:: password/quality/forbidden/chars

   Defines the characters and digits that are not allowed for passwords. For
   more information, see :ref:`users-passwords`.


.. envvar:: password/quality/length/min

   Sets the minimum length default for a password on a per UCS system basis for
   users not subject to a UDM password policy. The value ``yes`` applies checks
   from the :program:`python-cracklib`. The value ``sufficient`` does not
   include :program:`python-cracklib` checks. For more information, see
   :ref:`users-passwords`.


.. envvar:: password/quality/mspolicy

   Defines the standard Microsoft password complexity criteria. For more
   information, see :ref:`users-passwords`.

.. envvar:: password/quality/required/chars

   Defines individual characters/figures that are compulsory for passwords. For
   more information, see :ref:`users-passwords`.


.. envvar:: pkgdb/scan

   Controls if a UCS system stores installation processes in the software
   monitor. To turn it off, set the value ``no``. For more information see
   :ref:`computers-softwaremonitor`.

.. envvar:: portal/auth-mode

   Defines the authentication mode for the UCS portal. Set it to ``saml``, if
   you want to activate SAML for single sign-on login. For more information see
   :ref:`central-management-umc-login`.


.. envvar:: proxy/http

   Defines the HTTP proxy server on the UCS host system. For more information,
   see :ref:`computers-configuring-proxy-access`.


.. envvar:: proxy/no_proxy

   Defines a list of domains that are not used over a HTTP proxy. Entries are
   separated by commas. For more information, see
   :ref:`computers-configuring-proxy-access`.


.. envvar:: quota/logfile

   To log the activation of quotas to a file, specify the file in this variable.
   For more information, see :ref:`shares-quota-apply`.


.. envvar:: quota/userdefault

   To disable the evaluation of user quota during login, set the value to
   ``no``. For more information, see :ref:`shares-quota-apply`.


.. envvar:: radius/mac/whitelisting

   To only allow specific network devices access to a network through RADIUS,
   set the value to ``true``. For more information, see
   :ref:`ip-config-radius-configuration-mac-filtering`.


.. envvar:: radius/service-specific-password

   To use a dedicated user password for RADIUS instead of the domain password,
   set the value to ``true``. For more information, see
   :ref:`ip-config-radius-configuration-service-specific-password`.


.. envvar:: repository/mirror/server

   Defines another repository server as source for the local mirror. Default
   value: ``updates.software-univention.de``. For more information see
   :ref:`software-createrepo`.


.. envvar:: repository/online/component/.*/unmaintained

   Defines how to deal with unmaintained packages from additional repositories.
   To activate, set the value to ``yes``. For more information see
   :ref:`software-configrepo`.


.. envvar:: repository/online/server

   The repository server used to check for updates and download packages.
   Default value: ``updates.software-univention.de``. For more information see
   :ref:`computers-configuration-via-univention-configuration-registry`.


.. envvar:: samba/enable-msdfs

   To enable Microsoft Distributed File System (MSDFS), set the value to ``yes``
   and restart Samba. For more information, see :ref:`shares-msdfs`.


.. envvar:: samba/max/protocol

   Configures the file service protocol that Samba uses on UCS. The allowed
   values ``NT1``, ``SMB2``, and ``SMB3``. For more information, see
   :ref:`windows-samba4-fileservices`.


.. envvar:: samba4/sysvol/sync/cron

   Configures the synchronization time interval between Samba/AD domain
   controllers for the SYSVOL share. Default value is five minutes. For more
   information, see :ref:`windows-sysvolshare`.


.. envvar:: saml/idp/authsource

   Allows Kerberos authentication at the SAML identity provider. Change to
   ``univention-negotiate`` to activate. The default is ``univention-ldap``. For
   more information, see :ref:`domain-saml`.

.. envvar:: saml/idp/entityID/supplement/[identifier]

   Activates additional local identity providers for SAML on a UCS system
   serving as UCS Identity provider. To activate set the value to ``true``. For
   more information see :ref:`domain-saml-extended-configuration`.


.. envvar:: saml/idp/negotiate/filter-subnets

   Allows to restrict the Kerberos authentication at the SAML identity provider
   to certain IP subnets in the `CIDR notation
   <https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing>`_, for example
   ``127.0.0.0/16,192.168.0.0/16``. For more information, see
   :ref:`domain-saml`.

.. envvar:: saml/idp/selfservice/account-verification/error-descr

   Configures the error message description text for the :program:`Self
   Service`. The text shows up for users that login through SSO with an
   unverified and self registered user account. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.


.. envvar:: saml/idp/selfservice/account-verification/error-title

   Configures the error message title for the :program:`Self Service`. The title
   shows up for users that login through SSO with an unverified and self
   registered user account. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.


.. envvar:: saml/idp/selfservice/check_email_verification

   Controls if the SSO login denies logins from unverified and self registered
   user accounts. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.

.. envvar:: security/packetfilter/disabled

   To disable Univention firewall, set the value to ``true``. For more
   information, see :ref:`ip-config-packet-filter-with-univention-firewall`.


.. envvar:: self-service/backend-server

   Defines the UCS system where the backend of the :program:`Self Service` app
   is installed. For more information, see
   :ref:`user-management-password-changes-by-users-self-service`.

.. envvar:: server/password/change

   Enables or disables the password rotation on a UCS system. Per default the
   password rotation is activated. For more information, see
   :ref:`computers-hostaccounts`.


.. envvar:: server/password/interval

   Defines the interval in days to regeneratee the computer account password.
   The default is set to 21 days. For more information, see
   :ref:`computers-hostaccounts`.


.. envvar:: server/role

   TBD

.. TODO : Define UCRV server/role


.. envvar:: squid/auth/allowed_groups

   To limit the access to the Squid web proxy, define a list of group names
   separated by semicolon (``;``). For more information, see
   :ref:`proxy-userauth`.

.. envvar:: squid/allowfrom

   Configures additional networks to allow access to the Squid web proxy.
   Seperate the entries with blank spaces and use the CIDR notation, for example
   ``192.0.2.0/24``. For more information, see
   :ref:`ip-config-restriction-of-access-to-permitted-networks`.

.. envvar:: squid/basicauth

   To activate direct authentication for the Squid web proxy against the LDAP
   server, set the value to ``yes`` and restart Squid. For more information, see
   :ref:`proxy-userauth`.


.. envvar:: squid/cache

   To deactivate the caching function of the Squid web proxy, set the value to
   ``no``. For more information, see :ref:`ip-config-caching-of-web-content`.


.. envvar:: squid/httpport

   Configures the port for Squid web proxy, where the daemon listens for
   incoming connections. The default value is ``3128``. For more information,
   see :ref:`proxy-port`.


.. envvar:: squid/krb5auth

   To activate authentication through Kerberos for the Squid web proxy, set the
   value to ``yes`` and restart Squid. For more information, see
   :ref:`proxy-userauth`.


.. envvar:: squid/ntlmauth

   To activate authentication for the Squid web proxy against the NTLM
   interface, set the value to ``yes`` and restart Squid. For more information,
   see :ref:`proxy-userauth`.


.. envvar:: squid/ntlmauth/keepalive

   To deactivate further NTML authentication for subsequent HTML requests to the
   same website, set the value to ``yes``. For more information, see
   :ref:`proxy-userauth`.


.. envvar:: squid/webports

   Configures the list of permitted ports for the Squid web proxy. Separate
   entries with blank spaces. For more information, see
   :ref:`ip-config-permitted-ports`.


.. envvar:: sshd/permitroot

   Configures how the SSH daemon permits login for the user ``root``. The value
   ``without-password`` does not ask for the password interactively. The login
   requires the public SSH key. For more information, see
   :ref:`computers-ssh-login-to-systems`.


.. envvar:: sshd/port

   Configure the port that the SSH daemon uses to listen for connection. The
   default value is ``22``. For more information, see
   :ref:`computers-ssh-login-to-systems`.


.. envvar:: sshd/xforwarding

   Configures, if the SSH daemon allows X11 forwarding. Valid values are ``yes``
   and ``no``. For more information, see :ref:`computers-ssh-login-to-systems`.


.. envvar:: ssl/validity/host

   Records the expiry date of the local computer certificate on each UCS system.
   The value reflects the number of days since the 1970-01-01.


.. envvar:: ssl/validity/root

   Records the expiry date of the root certificate on each UCS system. The value
   reflects the number of days since the 1970-01-01.


.. envvar:: ssl/validity/warning

   Defines the warning period for the expiration check of the SSL/TLS root
   certificate. The default value is ``30`` days. See :ref:`domain-ssl`.

.. envvar:: system/stats

   Enables or disables the logging of the system status. The default value is
   ``yes``. For more information, see
   :ref:`computers-logging-the-system-status`.


.. envvar:: system/stats/cron

   Configures the runtimes when :command:`univention-system-stats` is run. The
   value follows the :ref:`cron syntax <cron-syntax>`. For more information, see
   :ref:`computers-logging-the-system-status`.


.. envvar:: timeserver

   Configures the first external NTP timeserver. For more information, see
   :ref:`basicservices-ntp`.


.. envvar:: timeserver2

   Configures the second external NTP timeserver. For more information, see
   :ref:`basicservices-ntp`.


.. envvar:: timeserver3

   Configures the third external NTP timeserver. For more information, see
   :ref:`basicservices-ntp`.


.. envvar:: ucs/web/theme

   Select the theme for |UCSWEB|. The value corresponds to a CSS file under
   :file:`/usr/share/univention-web/themes/` with the same name without filename
   extension.


.. envvar:: umc/self-service/account-deregistration/enabled

   To activate the :program:`Self Service` deregistration, set the variable to
   ``True``. For more information, see
   :ref:`user-management-password-changes-by-users-selfderegistration`.


.. envvar:: umc/self-service/account-verification/backend/enabled

   Enables or disables the account verification and request of new verification
   tokens for the :program:`Self Service`. For more information, see
   :ref:`user-management-password-changes-by-users-selfregistration-account-verification`.


.. envvar:: users/default/administrator

   Configures the default user name for the domain administrator. The value
   might be changed during an AD Takeover. For more information, see
   :ref:`windows-adtakeover-migrate`.
