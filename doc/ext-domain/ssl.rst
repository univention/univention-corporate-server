.. _extdom-ssl:

*********************************
Advanced SSL certificate handling
*********************************

.. _extdom-ssl-manage:

Managing additional certificates with :command:`univention-certificate`
=======================================================================

Every UCS domain has its own SSL certificate authority. The SSL certificates are
created automatically for all UCS systems during the installation
(|UCSPRIMARYDN|) or during the domain join (all other system roles).

The command :command:`univention-certificate` can be used to manage these
certificates, e.g., if it proves necessary to create a certificate for the
integration of an external system. The command is executed as ``root`` on the
|UCSPRIMARYDN|.

.. _extdom-ssl-storage:

Storage of the certificates
---------------------------

The certificates are stored in the directory :file:`/etc/univention/ssl/` on the
|UCSPRIMARYDN| and synchronized on all |UCSBACKUPDN| systems. A subdirectory
with the name of the certificate is kept in the directory
:file:`/etc/univention/ssl/` for every certificate, which contains the following
files:

:file:`req.pem`
   This file contains the original request with which the certificate
   was created.

:file:`openssl.cnf`
   This file contains the OpenSSL configuration at the time the
   certificate was created.

:file:`cert.pem`
   The file represents the actual certificate.

:file:`private.key`
   The file contains the private key for the certificate.

.. _extdom-ssl-list:

Displaying the certificates
---------------------------

The following command is used to display a list of all the available, valid
certificates:

.. code-block:: console

   $ univention-certificate list

An individual SSL certificate can be displayed with the following command:

.. code-block:: console

   $ univention-certificate dump -name fullyqualifiedhostname

.. _extdom-ssl-valid:

Checking the validity of a certificate
--------------------------------------

This command checks whether a certificate is valid or invalid:

.. code-block:: console

   $ univention-certificate check -name fullyqualifiedhostname

A certificate may be invalid because it has either been revoked or has expired.

.. _extdom-ssl-revoke:

Revoking a certificate
----------------------

The following command is used to revoke a certificate:

.. code-block:: console

   $ univention-certificate revoke -name fullyqualifiedhostname

It is then no longer valid, but remains stored in the file system. Certificates
of UMC computer objects do not need to be revoked manually.

.. _extdom-ssl-create:

Creating a certificate
----------------------

The following command can be used to create a new certificate:

.. code-block:: console

   $ univention-certificate new -name fullyqualifiedhostname

The fully qualified domain name of the computer should be given as the name. By
default the certificate is valid for five years. The standard value can be
changed by setting the |UCSUCRV| :envvar:`ssl/default/days`.

.. _extdom-ssl-sign:

Signing of certificate signing requests by the UCS certificate authority
========================================================================

A certificate signing request (CSR) is a request submitted to a certificate
authority (CA) to create a digital signature. A CSR typically occurs in the form
of a file. This section describes how a CSR is signed by the UCS CA.

:file:`CERTIFICATE`
   is the file name of the certificate to be created.

:file:`REQUEST`
   is the file with the CSR in either PEM or DER format. A file in PEM format is
   a text file containing a base64 encoded block enclosed between ``BEGIN
   CERTIFICATE`` and ``END CERTIFICATE``. A request in binary DER format must be
   first converted to the PEM format with the following command:

.. code-block:: console

   $ openssl req \
     -inform  der -in  request.der \
     -outform pem -out req.pem

The following command then processes the CSR and creates the certificate:

.. code-block:: console

   $ openssl ca -batch -config /etc/univention/ssl/openssl.cnf \
     -in REQUEST -out CERTIFICATE \
     -passin file:/etc/univention/ssl/password

