.. _ext-dom-ubuntu:

***********************************************
Integration of Ubuntu clients into a UCS domain
***********************************************

Univention Corporate Server allows the integration of Ubuntu clients. Initially
a standard Ubuntu installation needs to be performed. The following section
describes the configuration changes, which need to be made to integrate the
Ubuntu client into the UCS domain. After successful integration users can
authenticate on the Ubuntu clients with their standard UCS domain password and
username.

This configuration has been tested with Ubuntu 14.04 LTS, Ubuntu 16.04 LTS as
well as Kubuntu 14.04 LTS.

.. caution::

   In case a command fails or does not return the expected output,
   please make sure that all configuration options and files are entered
   and have been written as shown in this document. For example, some
   text editors do not preserve the indentation which is required for
   some configuration files.

.. _ubuntu-integration:

Integration into the LDAP directory and the SSL certificate authority
=====================================================================

After Ubuntu has been installed, some of it's configuration files need
to be modified. To simplify the setup, the default configuration of the
UCS Primary Directory Node should be copied to the Ubuntu system, for
example:

.. code-block:: console

   # Become root
   $ sudo bash <<"EOF"

   # Set the IP address of the UCS Primary Directory Node, 192.0.2.3 in this example
   export PRIMARY_DIRECTORY_NODE_IP=192.0.2.3

   mkdir /etc/univention
   ssh -n root@${PRIMARY_DIRECTORY_NODE_IP} 'ucr shell | grep -v ^hostname=' >/etc/univention/ucr_primary_directory_node
   echo "primary_directory_node_ip=${PRIMARY_DIRECTORY_NODE_IP}" >>/etc/univention/ucr_primary_directory_node
   chmod 660 /etc/univention/ucr_primary_directory_node
   . /etc/univention/ucr_primary_directory_node

   echo "${PRIMARY_DIRECTORY_NODE_IP} ${ldap_master}" >>/etc/hosts

   EOF

By default UCS only authenticated users can search in the LDAP
directory. As such, the Ubuntu client needs an account in the UCS domain
to gain read access to the LDAP directory:

.. code-block:: console

   # Become root
   $ sudo bash

   $ . /etc/univention/ucr_primary_directory_node

   # Download the SSL certificate
   $ mkdir -p /etc/univention/ssl/ucsCA/
   $ wget -O /etc/univention/ssl/ucsCA/CAcert.pem \
       http://${ldap_master}/ucs-root-ca.crt

   # Create an account and save the password
   $ password="$(tr -dc A-Za-z0-9_ </dev/urandom | head -c20)"
   $ ssh -n root@${ldap_master} udm computers/ubuntu create \
       --position "cn=computers,${ldap_base}" \
       --set name=$(hostname) --set password="${password}" \
       --set operatingSystem="$(lsb_release -is)" \
       --set operatingSystemVersion="$(lsb_release -rs)"
   $ printf '%s' "$password" >/etc/ldap.secret
   $ chmod 0400 /etc/ldap.secret

   # Create ldap.conf
   $ cat >/etc/ldap/ldap.conf <<__EOF__
   TLS_CACERT /etc/univention/ssl/ucsCA/CAcert.pem
   URI ldap://$ldap_master:7389
   BASE $ldap_base
   __EOF__

.. _ubuntu-sssd:

Configuration of the System Security Services Daemon (SSSD)
===========================================================

SSSD provides a set of daemons to manage access to remote directories
and authentication mechanisms.

.. code-block:: console

   # Become root
   $ sudo bash

   $ . /etc/univention/ucr_primary_directory_node

   # Install SSSD based configuration
   $ DEBIAN_FRONTEND=noninteractive apt-get -y install sssd libnss-sss libpam-sss libsss-sudo

   # Create sssd.conf
   $ cat >/etc/sssd/sssd.conf <<__EOF__
   [sssd]
   config_file_version = 2
   reconnection_retries = 3
   sbus_timeout = 30
   services = nss, pam, sudo
   domains = $kerberos_realm

   [nss]
   reconnection_retries = 3

   [pam]
   reconnection_retries = 3

   [domain/$kerberos_realm]
   auth_provider = krb5
   krb5_kdcip = ${primary_directory_node_ip}
   krb5_realm = ${kerberos_realm}
   krb5_server = ${ldap_master}
   krb5_kpasswd = ${ldap_master}
   id_provider = ldap
   ldap_uri = ldap://${ldap_master}:7389
   ldap_search_base = ${ldap_base}
   ldap_tls_reqcert = never
   ldap_tls_cacert = /etc/univention/ssl/ucsCA/CAcert.pem
   cache_credentials = true
   enumerate = true
   ldap_default_bind_dn = cn=$(hostname),cn=computers,${ldap_base}
   ldap_default_authtok_type = password
   ldap_default_authtok = $(cat /etc/ldap.secret)
   __EOF__
   $ chmod 600 /etc/sssd/sssd.conf

   # Install auth-client-config
   $ DEBIAN_FRONTEND=noninteractive apt-get -y install auth-client-config

   # Create an auth config profile for sssd
   $ cat >/etc/auth-client-config/profile.d/sss <<__EOF__
   [sss]
   nss_passwd=   passwd:   compat sss
   nss_group=    group:    compat sss
   nss_shadow=   shadow:   compat
   nss_netgroup= netgroup: nis

   pam_auth=
           auth [success=3 default=ignore] pam_unix.so nullok_secure try_first_pass
           auth requisite pam_succeed_if.so uid >= 500 quiet
           auth [success=1 default=ignore] pam_sss.so use_first_pass
           auth requisite pam_deny.so
           auth required pam_permit.so

   pam_account=
           account required pam_unix.so
           account sufficient pam_localuser.so
           account sufficient pam_succeed_if.so uid < 500 quiet
           account [default=bad success=ok user_unknown=ignore] pam_sss.so
           account required pam_permit.so

   pam_password=
           password requisite pam_pwquality.so retry=3
           password sufficient pam_unix.so obscure sha512
           password sufficient pam_sss.so use_authtok
           password required pam_deny.so

   pam_session=
           session required pam_mkhomedir.so skel=/etc/skel/ umask=0077
           session optional pam_keyinit.so revoke
           session required pam_limits.so
           session [success=1 default=ignore] pam_sss.so
           session required pam_unix.so
   __EOF__
   $ auth-client-config -a -p sss

   # Restart sssd
   $ service sssd restart

The commands :command:`getent passwd` and :command:`getent
group` should now also display all users and groups of the UCS
domain.

.. _ubuntu-login:

Configuring user logins
=======================

The home directory of a user should be created automatically during
login:

.. code-block:: console

   # Become root
   $ sudo bash

   $ cat >/usr/share/pam-configs/ucs_mkhomedir <<__EOF__
   Name: activate mkhomedir
   Default: yes
   Priority: 900
   Session-Type: Additional
   Session:
       required    pam_mkhomedir.so umask=0022 skel=/etc/skel
   __EOF__

   $ DEBIAN_FRONTEND=noninteractive pam-auth-update --force

During login users should also be added to some system groups:

.. code-block:: console

   # Become root
   $ sudo bash

   $ echo '*;*;*;Al0000-2400;audio,cdrom,dialout,floppy,plugdev,adm' \
      >>/etc/security/group.conf

   $ cat >>/usr/share/pam-configs/local_groups <<__EOF__
   Name: activate /etc/security/group.conf
   Default: yes
   Priority: 900
   Auth-Type: Primary
   Auth:
       required    pam_group.so use_first_pass
   __EOF__

   $ DEBIAN_FRONTEND=noninteractive pam-auth-update --force

By default the Ubuntu login manager only displays a list of local users
during login. After adding the following lines an arbitrary user name
can be used:

.. code-block:: console

   # Become root
   $ sudo bash

   # Add a field for a user name, disable user selection at the login screen
   $ mkdir /etc/lightdm/lightdm.conf.d
   $ cat >>/etc/lightdm/lightdm.conf.d/99-show-manual-userlogin.conf <<__EOF__
   [SeatDefaults]
   greeter-show-manual-login=true
   greeter-hide-users=true
   __EOF__

Kubuntu 14.04 uses ``AccountService``, a D-Bus interface for user
account management, which ignores the
:file:`/etc/lightdm.conf` file. Since there is no
configuration file for ``AccountService`` the login theme needs to be
changed to *classic* under :menuselection:`System
Settings --> Login Screen (LightDM)`.

With these settings the login for domain members should be possible
after a restart of LightDM or a reboot.

.. _ubuntu-kerberos:

Kerberos integration
====================

Every UCS domain provides a Kerberos domain. Since Kerberos relies on
DNS, the Ubuntu client should use a UCS Directory Node (|UCSPRIMARYDN|,
|UCSBACKUPDN| or |UCSREPLICADN|) as its DNS server. The following steps
provide an example configuration for Kerberos:

.. code-block:: console

   # Become root
   $ sudo bash

   $ . /etc/univention/ucr_primary_directory_node

   # Install required packages
   $ DEBIAN_FRONTEND=noninteractive apt-get install -y heimdal-clients ntpdate

   # Default krb5.conf
   $ cat >/etc/krb5.conf <<__EOF__
   [libdefaults]
       default_realm = $kerberos_realm
       kdc_timesync = 1
       ccache_type = 4
       forwardable = true
       proxiable = true
       default_tkt_enctypes = arcfour-hmac-md5 des-cbc-md5 des3-hmac-sha1 des-cbc-crc des-cbc-md4 des3-cbc-sha1 aes128-cts-hmac-sha1-96 aes256-cts-hmac-sha1-96
       permitted_enctypes = des3-hmac-sha1 des-cbc-crc des-cbc-md4 des-cbc-md5 des3-cbc-sha1 arcfour-hmac-md5 aes128-cts-hmac-sha1-96 aes256-cts-hmac-sha1-96
       allow_weak_crypto=true

   [realms]
   $kerberos_realm = {
      kdc = $primary_directory_node_ip $ldap_master
      admin_server = $primary_directory_node_ip $ldap_master
      kpasswd_server = $primary_directory_node_ip $ldap_master
   }
   __EOF__

   # Synchronize the time with the UCS system
   $ ntpdate -bu $ldap_master

   # Test Kerberos: kinit will ask you for a ticket and the SSH login to the Primary Directory Node should work with ticket authentication:
   $ kinit Administrator
   $ ssh -n Administrator@$ldap_master ls /etc/univention

   # Destroy the kerberos ticket
   $ kdestroy

.. _ubuntu-limits:

Limitations of the Ubuntu domain integration
============================================

It is currently not possible to change the user password at the LightDM
login manager. Instead, the password can be changed via the
:command:`kpasswd` command after login or via the UMC module
*Change password*.

.. _ubuntu-ref:

Additional references
=====================

* `<https://help.ubuntu.com/community/LDAPClientAuthentication>`_

* `<https://help.ubuntu.com/community/SingleSignOn>`_

* `<https://help.ubuntu.com/community/PamCcredsHowto>`_

* `<http://labs.opinsys.com/blog/2010/03/26/user-management-with-sssd-on-shared-laptops/>`_

