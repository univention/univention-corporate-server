.. _domain-backup2master:

Converting a |UCSBACKUPDN| backup to the new |UCSPRIMARYDN|
===========================================================

.. highlight:: console

A UCS domain consists of only one |UCSPRIMARYDN|, but is not limited in the
number of |UCSBACKUPDN|. A |UCSBACKUPDN| stores all the domain data and all SSL
security certificates as read-only copies. However, in contrast to the
|UCSPRIMARYDN|, writing changes are not allowed.

Any |UCSBACKUPDN| can be converted to a |UCSPRIMARYDN|. There are two typical
scenarios for this:

* In an emergency if the hardware of the |UCSPRIMARYDN| fails.

* To replace a fully functional |UCSPRIMARYDN| with new hardware or changing the
  architecture from *i386* to *amd64*.

.. caution::

   The conversion of a |UCSBACKUPDN| to a |UCSPRIMARYDN| is a serious
   configuration change and should be prepared carefully. The conversion cannot
   be reversed.

   The |UCSPRIMARYDN| that is going to be replaced has to be shut down before
   the conversion. It must not be powered on during or after the conversion!

   Before the conversion, the installed software packages and the current
   configuration has to be compared between the |UCSPRIMARYDN| and
   |UCSBACKUPDN|. If the |UCSPRIMARYDN| is not available anymore, use a file
   backup. After the conversion, all possibly remaining references of the old
   |UCSPRIMARYDN| have to be removed or changed to the new |UCSPRIMARYDN|.

The conversion primarily involves the changeover of the services relevant for
authentication such as LDAP, DNS, Kerberos and Samba. The installed software
needs to be adjusted manually (this can be done using the UMC modules
:guilabel:`App Center` or :guilabel:`Package Management`).

For example, if the mail component was installed on the previous |UCSPRIMARYDN|,
it will not be automatically installed on the new |UCSPRIMARYDN| after the
conversion. To minimize manual changes after the conversion, please consider
:ref:`domain-fault-tolerant`.

If additional LDAP schema packages were installed on the |UCSPRIMARYDN|, they
must also be installed on the |UCSBACKUPDN| prior to the conversion. The
package list of the old |UCSPRIMARYDN| should be saved prior to the promotion in
order to allow a subsequent comparison of the installed packages. The package
list can be created with the following command:

.. code-block::

   $ dpkg --get-selections \* >> dpkg.selection


This file should be compared with the same output on the |UCSBACKUPDN|.  Missing
packages should then be installed on the |UCSBACKUPDN|. Especially those
packages that install a LDAP schema are absolutely necessary. The following
command executed on the |UCSPRIMARYDN| will list all affected packages:

.. code-block::

   $ dpkg -S /etc/ldap/schema/*.schema \
   > /usr/share/univention-ldap/schema/*.schema


To simply install all packages of the |UCSPRIMARYDN| also on the |UCSBACKUPDN|,
use the previously created file :file:`dpkg.selection` of the |UCSPRIMARYDN| and
run the following command on the |UCSBACKUPDN|:

.. code-block::

   $ dpkg --set-selections < dpkg.selection
   $ apt-get dselect-upgrade

In addition, the |UCSUCR| inventory needs to be saved so that it is possible to
compare the configuration adjustments on the new |UCSPRIMARYDN|. The following
files on the |UCSPRIMARYDN| need to be compared with those on the |UCSBACKUPDN|:

* :file:`/etc/univention/base.conf`
* :file:`/etc/univention/base-forced.conf`

UCS saves a copy of those files every night to
:file:`/var/univention-backup/ucr-backup_%Y%m%d.tgz`.

The conversion of a |UCSBACKUPDN| to the new |UCSPRIMARYDN| is performed by
running the command :command:`/usr/lib/univention-ldap/univention-backup2master`
on the |UCSBACKUPDN|. The system must be rebooted after the conversion. The
process is logged to :file:`/var/log/univention/backup2master.log` The following
steps are performed by :command:`univention-backup2master`:

* Checking the environment: The system must be a |UCSBACKUPDN| that already
  joined the domain. Additionally, it is checked if the |UCSPRIMARYDN| can be
  resolved via DNS and if the repository server can be reached. Also, the
  |UCSPRIMARYDN| must be powered off and not reachable anymore.

* Now, the most important services OpenLDAP, Samba, Kerberos and |UCSUDN| and
  Listener will be stopped. Important |UCSUCRV|, such as :envvar:`ldap/master`
  and :envvar:`server/role` will be changed. The UCS Root CA certificate will be
  available via the webserver on the |UCSBACKUPDN|. All mentioned services will
  be started again.

* The DNS SRV record ``kerberos-adm`` will be changed from the old to the new
  |UCSPRIMARYDN|.

* If present, the Univention S4 Connector (see :ref:`windows-s4-connector`) will
  be removed from the computer object of the old |UCSPRIMARYDN| and will be
  scheduled for re-configuration on the new |UCSPRIMARYDN|.

* The server role of the new |UCSPRIMARYDN| will be changed to
  ``domaincontroller_master`` in the OpenLDAP directory service. The DNS SRV
  record ``_domaincontroller_master._tcp`` will also be adjusted.

* If present, all entries of the old |UCSPRIMARYDN| will be removed from the
  local Samba directory service. Additionally, the FSMO roles will be
  transferred to the new |UCSPRIMARYDN|.

* The computer object of the old |UCSPRIMARYDN| will be deleted from OpenLDAP.

* The OpenLDAP directory service will be searched for any remaining references
  to the old |UCSPRIMARYDN|. All found references (e.g. DNS records) are shown
  and suggested to be fixed. The suggested fixes have to be checked and
  confirmed one by one.

* Finally, the package :program:`univention-server-backup` will be replaced by
  :program:`univention-server-master`.

Subsequently, the LDAP directory on the new |UCSPRIMARYDN| and the |UCSUCR|
values on all UCS systems of the domain should be checked for any remaining
references to the hostname or the IP address of the old |UCSPRIMARYDN|. Those
references need to be adjusted to the new |UCSPRIMARYDN|, too.
