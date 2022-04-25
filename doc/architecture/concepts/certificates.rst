.. _concept-certificates:

Certificate infrastructure
==========================

The certificate infrastructure in a domain operated with Univention Corporate
Server (UCS) ensures the trust context between all participants. The first
domain node creates its own certificate authority (CA) for the domain. For
more information see the `Wikipedia article Certificate authority
<w-certificate-authority_>`_.

UCS uses Transport Layer Security (TLS). The UCS Primary Directory Node creates
the CA on behalf of the domain during its installation and signs certificates
for other systems that join the domain. All certificates have an expiration
date. Backup Directory Nodes in the domain repeatedly pull all certificates from
the Primary Domain Controller to allow administrators to promote one of them to a
Primary Directory Node any time, if needed.

Services in the UCS domain also use the certificates created by UCS.
Administrators can configure alternative certificates for end-user or internet
facing services with certificates issued by third parties, for example `Let's
Encrypt <lets-encrypt_>`_.

.. TODO : Two reviewers provided feedback on this section and wanted to see
   links to UCR variables and more information. But the current detail level
   prohibits it at this point. Maybe a later section can refer to this part and
   at the same time also provide the interesting links. It would stay in the
   scope. See https://git.knut.univention.de/univention/ucs/-/merge_requests/358#note_62484

The domain systems use the certificates for secure communication between each
other over the computer network, for example for domain database replication and
the web interface of the UCS management system. Communication clients need to
know the public key of the domain's CA to validate the public key of the
certificate.
