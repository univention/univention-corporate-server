.. _concept-certificates:

Certificate infrastructure
==========================

The certificate infrastructure in a domain operated with Univention Corporate
Server (UCS) ensures the trust context between all participants. The first
domain controller creates its own certificate authority (CA) for the domain. For
more information see the `Wikipedia article Certificate authority
<w-certificate-authority_>`_.

UCS uses Transport Layer Security (TLS). The UCS Primary Directory Node creates
the CA on the behalf of the domain during its installation and signs
certificates for other systems that join the domain. All certificates have an
expiration date. The Primary Directory Node regularly copies all CA certificates
to the Backup Directory Nodes in the domain.

The domain systems use the certificates for secure communication between each
other over the computer network, for example for domain database replication and
the web interface of the UCS management system. Communication clients need to
know the public key of the domain's CA to validate the public key of the
certificate.
