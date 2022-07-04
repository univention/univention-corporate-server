.. _appliance-create:
.. _appliance-intro:

************************************
Creating a UCS appliance/cloud image
************************************

This section describes how to set up an appliance based on UCS 5.0. This type of
appliance can also be used to provide preconfigured instances as a cloud service
provider. The creation of images for typical virtualization solutions is another
possible application scenario, see :ref:`appliance-create-virt`.

.. _appliance-installbase:

Performing the basic installation
=================================

The basic installation is performed using the standard UCS installer. Further
information on the individual options can be found in the UCS manual. The
installation should be performed in a virtualization solution. In this example,
the installation is performed in QEMU. A ``qcow2`` image should be selected for the
hard drive for the virtual machine. ``qcow2`` images can be converted to different
virtualization formats such as VirtualBox or VMware using a tool provided by
Univention, see :ref:`appliance-create-virt`.

The following settings are configured for the basic image:

* The installation language can be selected as required. The locale of the
  system is set based on the selected language. If you want to be able to use
  the appliance in more than one language, you can add another locale at a later
  point in time.

* A preselection is made for the time zone which is then adapted subsequently
  by the users of the appliance.

* The keyboard layout is only relevant for local logins; it is not important
  for the web-based configuration.

* A configuration via DHCP is the most practical presetting for appliance
  images. The Univention Installer attempts to perform a DHCP request in the
  scope of the network configuration. The network configuration is only
  performed via DHCP if this is successful, i.e., an IP address must be assigned
  to the appliance for the duration of the setup. This can be done with an *IP
  client* object in the |UCSUMC|.

* In the next step, the initial password is set for the root user. This root
  password is changed by the end user during the commissioning of the appliance
  image.

* The partitioning can be performed as required, e.g., by using a LVM. For an
  image that will be used in a cloud setup, a single root partition should be
  used. This allows growing the root partition based on the selected instance
  disk size.

Once the basic installation is complete, a dialogue is shown in which you can
select whether to create a new UCS domain or join an existing domain. To create
the appliance, :kbd:`Control + Q` must be pressed at this point to interrupt the
process. The installation continues for a short period of time, during which the
*Starting Univention System Setup* message appears and the systems then
restarts.

The installation of the basic image is now complete. Following a reboot, the
user of the appliance is shown the dialogue for adjusting the configuration, see
:ref:`appliance-use`.

In most cases, the appliance needs to be preconfigured with a certain selection
of software. The installation is usually performed via the Univention App
Center, which, however, is not yet available at this point in time. The
installation is thus performed via the command line. UCS standard components can
be installed using the corresponding package names, e.g.

.. code-block:: console

   $ univention-install univention-printserver


Packages from the Univention App Center are installed with the command
:command:`univention-app install` once a valid license is available. The ID of
an application can be retrieved with the command :command:`univention-app list`:

.. code-block:: console

   $ univention-app install APPID


The system now needs to be shut down cleanly without file systems still being
mounted.

The ``qcow2`` image (i.e., the hard drive of the virtual machine) is now copied. If
the *default* storage pool of ``libvirtd`` was used, the image is stored in the
directory :file:`/var/lib/libvirt/images/`.

Additional steps are required if the image is to be used in Amazon EC2 (see
:ref:`appliance-create-ec2`), OpenStack (see :ref:`appliance-create-openstack`)
or as a VMware / VirtualBox appliance (see :ref:`appliance-create-virt`).

.. _appliance-create-ec2:

Providing an image for Amazon EC2
---------------------------------

The following adjustments need to be made for an image that is to be used in
Amazon EC2.

The following |UCSUCR| variables can be used to generate the GRUB configuration
in this format additionally. The boot loader configuration is also adapted:

.. code-block:: console

   $ DEV='/dev/xvda' GRUB='(hd0)'
   $ grub-mkdevicemap ||
   > echo "${GRUB} ${DEV}" >/boot/grub/device.map
   $ append="$(ucr get grub/append |
   > sed -re "s|/dev/sda|${DEV}|g;s|(no)?splash||g")"
   $ xargs -d'\n' ucr set <<__UCR__
   grub/append=${append}
   grub/boot=${DEV}
   grub/root=${DEV}1
   grub/bootsplash=no
   grub/quiet=no
   grub/rootdelay=0
   grub/timeout=0
   grub/terminal=console serial
   grub/serialcommand=serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
   __UCR__
   $ update-initramfs -uk all
   $ update-grub

The initial login to the EC2 instance is performed via a SSH host key. To
prevent SSH logins from occurring with the default root password of the standard
image during commissioning of the instance, the initial root password is
removed. The following |UCSUCR| variable configures this start mode:

.. code-block:: console

   $ usermod -p \* root
   $ ucr set server/amazon=true


The name server should be set; in this example to ``OpenDNS``. Additionally, the
timeout when waiting for a DHCP request answer is lowered.

.. code-block:: console

   $ ucr set nameserver1=208.67.222.222 dns/forwarder1=208.67.222.222
   $ ucr unset nameserver2 nameserver3
   $ ucr unset dns/forwarder2 dns/forwarder3
   $ ucr set interfaces/eth0/type=dhcp dhclient/options/timeout=12
   $ ucr set timeserver=169.254.169.123  # AWS internal


.. _appliance-create-openstack:

Providing an image for OpenStack
--------------------------------

The provisioning for OpenStack images occurs via Cloud-Init (see
:ref:`appliance-use-cloudinit`). Cloud-Init is a standardized solution for
configuration of an image. Cloud-Init checks a range of data sources for an
existing configuration. The :program:`univention-cloud-init` package must be
installed to prepare an image for provisioning via Cloud-Init:

.. code-block:: console

   $ univention-install cloud-init


The local :program:`Firefox` session should not be started when running as an
OpenStack instance.

.. code-block:: console

   $ ucr set system/setup/boot/start=false


The initial login to the OpenStack instance is performed via a SSH host key. To
prevent SSH logins from occurring with the default root password of the standard
image during commissioning of the instance, the initial root password is
removed.

.. code-block:: console

   $ usermod -p \* root


.. _appliance-create-virt:

Providing an image for VMware/VirtualBox
----------------------------------------

Virtualization images for :program:`VirtualBox`, :program:`VMware Player` and
:program:`VMware ESX` can also be created on the basis of the ``qcow2`` images
above. The package :program:`generate-appliance` provides tools for this.

The :command:`generate_appliance` tool must be started and the ``qcow2`` image
selected with the parameter ``-s``:

.. code-block:: console

   $ generate_appliance -s appliance.qcow2


The virtual machine is assigned one CPU and a gigabyte of RAM as standard. If
the appliance has a higher storage or CPU power requirement, the parameter
``-m`` can be used to specify a different quantity of RAM in
megabytes and ``-c`` can be used to assign a different number of
CPUs. The parameters ``--vendor`` and
``--product`` can be used to specify a vendor and product name.

By default three different virtualization images are generated from the
``qcow2`` image. The generation for a type can be suppressed using the
respectively given option:

* Zipped VMware compatible images (e.g. for :program:`VMware Player`), can be
  suppressed with ``--no-vmware``

* :program:`VirtualBox` OVA image, can be suppressed with
  ``--no-ova-virtualbox``

* :program:`VMware ESX` OVA image, can be suppressed with
  ``--no-ova-esxi``

.. _appliance-use-auto:

Automatic configuration of an appliance
=======================================

Instead of an interactive configuration of the appliance by the user, it can
also be performed automatically. The automatic configuration can either be
performed via :program:`cloud-init` (a general tool for the provision of cloud
images) or a Univention appliance mode profile file.

.. _appliance-use-auto-profile:

Automatic configuration with a UCS appliance mode profile file
--------------------------------------------------------------

Automatic configuration with the UCS appliance mode requires creating a profile
file :file:`/var/cache/univention-system-setup/profile`. Example configuration:

::

   hostname="ucs"
   domainname="testdom.local"
   windows/domain="TESTDOM"
   ldap/base="dc=testdom,dc=local"
   root_password="univention"

   locale/default="de_DE.UTF-8:UTF-8"
   components="univention-s4-connector univention-samba4"
   packages_install="univention-s4-connector univention-samba4"
   packages_remove=""

   server/role="domaincontroller_master"

   interfaces/eth0/type=""
   interfaces/eth0/address="192.0.2.2"
   interfaces/eth0/netmask="255.0.0.0"
   interfaces/eth0/network="10.0.0.0"
   interfaces/eth0/broadcast="10.255.255.255"
   dns/forwarder1="192.0.2.2"
   gateway="192.0.2.1"


If :envvar:`interfaces/eth0/type` is set to ``dynamic``, DHCP is used for the
network configuration.

Then the :command:`/usr/lib/univention-system-setup/scripts/setup-join.sh` tool
needs to be run once. Then Apache and the UMC server need to be restarted:

.. code-block:: console

   $ systemctl restart apache2 univention-management-console-server


.. _appliance-use-cloudinit:

Automatic configuration of an appliance with Cloud-Init
-------------------------------------------------------

.. note::

   This chapter is not up-to-date with UCS 5.

Cloud-Init works on a configuration file in the cloud configuration format. The
configuration file is provided by the respective cloud service; the type of
provision differs from cloud solution to cloud solution. It is currently only
possible to provide a |UCSPRIMARYDN|.

The configuration file may be adapted for different scenarios. To setup a
domain, the ``ucs_setup`` section is required. Note that the supplied
``ldap_base`` is used in other configuration sections, as well.

The following includes an example file with which a |UCSPRIMARYDN| can be
provided. In addition, several files are generated on the system: the UCS
license to be installed and a file with the apps to be installed from the
Univention App Center. The license in this example is the default *core edition
license*. More information about requesting a proper license can be found in
:ref:`appliance-license`.

Two example hook scripts are generated which are called after setup is finished:
One calls :command:`wget` for a given URL, which could be used to signal an
external service that the provisioning of the instance is done.

.. code:: yaml

   #cloud-config
   #
   ucs_setup:
     hostname: myucsprimary
     domainname: ucs.local
     windowsdomain: UCS
     ldap_base: dc=ucs,dc=local
     rootpassword: univention
     defaultlocale: de_DE.UTF-8:UTF-8
     components:
     packages_install:
     packages_remove:
   write_files:
   -   content: |
         dn: cn=admin,cn=license,cn=univention,dc=ucs,dc=local
         objectClass: top
         objectClass: univentionLicense
         objectClass: univentionObject
         univentionObjectType: settings/license
         univentionLicenseEndDate: unlimited
         univentionLicenseModule: admin
         cn: admin
         univentionLicenseBaseDN: UCS Core Edition
         univentionLicenseUsers: unlimited
         univentionLicenseServers: unlimited
         univentionLicenseManagedClients: unlimited
         univentionLicenseCorporateClients: unlimited
         univentionLicenseVirtualDesktopUsers: 0
         univentionLicenseVirtualDesktopClients: 0
         univentionLicenseSupport: 0
         univentionLicensePremiumSupport: 0
         univentionLicenseVersion: 2
         univentionLicenseType: UCS
         univentionLicenseSignature: ZjofoUmITUqpyF5q+AfE1i6EwsKXGWYnkh3JLJH3/bXqvD26nG
          aLa+cpcr6g9Stkx2Lslh1feGCpsdvowkA3T+SFtPHSX0Fds78QgyatoiFlA6mbbtMf3ABbMfW9Glt
          IZBbxxDFD+hMO/7yOHwaFZM3xb1I2ToJ1D2+xvOxrZe2SCZd4KJIXpupnmJnAC/D4Y9iqHPytVPU3
          QlI6zXnGU5q47RN/tdXLTpV7mHoiXRWh282TNOlnEiiQxwiQ4u2ghWE1x/EWY/CXvZm0PQcsFqGyB
          v72WdEUOex1Yuf3BgZ7QfLOQ2XIv6KPKCyYqZqlSNp8Xk+IpKjDqL+aq0oyeg==
       owner: root:root
       path: /var/cache/univention-system-setup/license
       permissions: '0400'
   -   content: |
         simplesamlphp
         adconnector
       owner: root:root
       path: /var/cache/univention-system-setup/installapps
       permissions: '0400'
   -   content: |
         #!/bin/sh
         wget http://myURL/page?myparam=myValue
       owner: root:root
       path: /usr/lib/univention-system-setup/appliance-hooks.d/90_wget_url
       permissions: '0755'


The file with the apps to be installed contains a list of IDs of applications
from the |UCSAPPC|, see :ref:`appliance-installbase`. The list in the example
above installs the :program:`AD Connector` and the :program:`SAML integration` on the
provided |UCSPRIMARYDN|.

.. _appliance-license:

License management in cloud instances
-------------------------------------

By default a UCS installation has a *core edition license*. An updated license
from Univention is required in order to use the App Center. For standard
installations it is sent to the user by email and then set up in the |UCSUMC|.

Cloud service providers have the possibility of retrieving UCS licenses via an
API, i.e., if a new instance is to be created for a customer, the license can be
retrieved via the API and then installed in the provided instance directly.

Access to the license server requires a user name and a password. These can be
requested from `Univention contact <https://www.univention.com/contact/>`_.
In this document, ``https://license.univention.de/shop/example/`` is used as an
example URL for the license server.

.. _appliance-license-api:

API for retrieving UCS licenses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The licenses are retrieved via HTTPS from the Univention license server
``license.univention.de``. The retrieval can be performed completely with
:command:`wget`.

Firstly, a session with the license server must be opened, in this case with the
user name ``univention`` and the password ``secret`` as an example. It is also
possible to request more than one license in one session.

.. code-block:: console

   $ wget \
   > --keep-session-cookies \
   > --save-cookies cookie.db \
   > --load-cookies cookie.db \
   > --post-data='username=univention&password=secret' \
   > https://license.univention.de/shop/example/


A license can also be ordered with a POST request via
:command:`wget`.

.. note::

   Special characters such as blank spaces must be escaped in URL-encoded
   syntax, see `<https://en.wikipedia.org/wiki/Percent-encoding>`_ for
   details.

.. code-block:: console

   $ wget \
   > --keep-session-cookies \
   > --save-cookies cookie.db \
   > --load-cookies cookie.db \
   > --post-data='kundeEmail=customer@example&'\
   > 'kundeUnternehmen=New%20Customern&'\
   > 'EndDate=27.11.2015&'\
   > 'BaseDN=dc%3Ddrei%2Cdc%3Dzwei%2Cdc%3Dtest&'\
   > 'Servers=0&'\
   > 'Support=0&'\
   > 'PremiumSupport=0&'\
   > 'Users=100&'\
   > 'ManagedClients=0&'\
   > 'CorporateClients=0&'\
   > 'VirtualDesktopUsers=0&'\
   > 'VirtualDesktopClients=0&'\
   > 'Type=UCS' \
   > https://license.univention.de/shop/example/order


If the order is successful, the HTTP status code ``202`` is returned. The HTML
data includes the tag ``orderid``, which identifies the order number of a
successful order:

::

   ...
   <span id="orderid">21</span>
   ...

If the order fails, a HTTP status code ``4xx`` is returned and the ``details`` tag
includes additional information, e.g.:

::

   ...
   <span id="details">Not a valid date: u'27.11.201'</span>
   ...


Should it not be possible to process an order due to a server error, ``5xx`` is
output as the return code. The order can then be repeated at a later point in
time.

Following ordering of a license, it takes a few seconds before the license is
generated. It can then be retrieved in LDIF format using the order number. If
the request above returns e.g. the order number ``465``, the file name is thus
:file:`465.ldif`. The request specified below waits for the availability of the
license for up to sixty seconds:

.. code-block:: console

   $ wget \
   > --keep-session-cookies \
   > --save-cookies cookie.db \
   > --load-cookies cookie.db \
   > https://license.univention.de/shop/example/orders/465.ldif


