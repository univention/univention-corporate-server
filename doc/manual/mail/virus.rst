.. _mail-virus:

Identification of viruses and malware
=====================================

The UCS mail services include virus and malware detection via the
:program:`univention-antivir-mail` package, which is automatically set up during
the setup of the mail server package. The virus scan can be deactivated with
the |UCSUCRV| :envvar:`mail/antivir`.

All incoming and outgoing e-mails are scanned for viruses. If the scanner
recognizes a virus, the e-mail is sent to quarantine. That means that the e-mail
is stored on the server where it is not accessible to the user. The original
recipient receives a message per e-mail stating that this measure has been
taken. If necessary, the administrator can restore or delete this from the
:file:`/var/lib/amavis/virusmails/` directory. Automatic deletion is not
performed.

The :program:`AMaViSd-new` software serves as an interface between the mail
server and different virus scanners. The free virus scanner ClamAV is included
in the package and enters operation immediately after installation. The
signatures required for virus identification are procured and updated
automatically and free of charge by the Freshclam service.

Alternatively or in addition, other virus scanners can also be integrated in
AMaViS. Postfix and AMaViS need to be restarted following changes to the AMaViS
or ClamAV configuration.
