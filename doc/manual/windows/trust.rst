.. _windows-trust:

Trust relationships
===================

Trust relationships between domains make it possible for users from one domain
to log in to computers from another domain.

In general, Windows trust relations can be *unidirectional* or *bidirectional*.
Technically a bidirectional trust is simply realized as two unidirectional
trusts, one in each direction.

The terminology of unidirectional trusts depends on the perspective of either
the trusting or trusted domain: From the perspective of the trusting domain, the
trust is called *outgoing*. From the perspective of the trusted domain, the
trust is called *incoming*.

In UCS, outgoing trust (UCS trusts Windows) is not supported. As a consequence,
bidirectional trust is not supported either.

When setting up and using the trust relationship the domain controllers of both
domains must be able to reach each other over the network and identify each
other via DNS. At least the fully qualified DNS names of the domain controllers
of the respective remote domain must be resolvable to allow communication
between both domains to work. This can be achieved by configuring conditional
DNS forwarding in both domains.

The following example assumes, that the UCS Samba/AD DC |UCSPRIMARYDN|
``primary.ucsdom.example`` has the IP address ``192.0.2.10`` and that the Active
Directory domain controller ``dc1.addom.example`` of the remote domain has the
IP address ``192.0.2.20``.

On the UCS side the conditional forwarding of DNS queries can be set up as
``root`` with the following commands:

.. code-block:: console

   $ cat >>/etc/bind/local.conf.samba4 <<__CONF__
   > zone "addom.example" {
   >   type forward;
   >   forwarders { 192.0.2.20; };
   > };
   > __CONF__
   $ systemctl restart bind9

The success can be checked by running:

.. code-block:: console

   $ host dc1.addom.example

In addition, it may be useful to create a static entry for the domain controller
of the remote Active Directory domain in the file :file:`/etc/hosts`:

.. code-block:: console

   $ ucr set hosts/static/192.0.2.20=dc1.addom.example


On a Windows AD DC, a so-called *conditional forwarding* can be set up for the
UCS domain via the DNS server console.

Trust relationships can only be configured on domain controllers but
they affect the whole domain.

After this preliminary work, the trust relationship can be established directly
from the command line of the UCS Samba/AD DC using the tool
:command:`samba-tool`:

.. code-block:: console

   $ samba-tool domain trust create addom.example \
   > -k no -UADDOM\\Administrator%ADAdminPassword \
   > --type=external --direction=incoming

The trust can be checked using the following commands:

.. code-block:: console

   $ samba-tool domain trust list
   $ wbinfo --ping-dc –domain=addom.example
   $ wbinfo --check-secret –domain=addom.example


After the setup, a UCS user should be able to log in to systems of the remote
Active Directory domain. Users must either use the format ``UCSDOM\username`` as
login name or their Kerberos principal in the notation
``username@ucsdom.example``.
