The deprecated ``libnss-ldap`` and ``libpam-ldap`` have been replaced with ``sssd``.
``sssd`` is currently used for users only. This also means that ``nscd`` is not used
any longer for the ``passwd`` related system calls (but it still is used as cache for
``hosts`` resolution). The UCR variables ``nscd/passwd/.`` are not used any longer.
The ``sssd`` is configured via ``/etc/sssd/sssd.conf`` which is generated from a
UCR template now. ``sssd`` additionally reads configuration sub files from the directory
``/etc/sssd/conf.d``, which can be used in case options need to be customized differently
from what the UCR template initially supports. Please note that ``sssd`` doesn't support
resolving ``shadow`` information at all, so e.g. ``pam_unix`` will not be able to read
``shadow`` related info for domain users (so there's a difference between domain users
managed in UDM/LDAP and traditional Linux local accounts).
Please also note that UCS currently still uses ``pam_krb5`` separately from ``sssd``,
as UCS and Samba use Heimdal Kerberos, while ``sssd`` may be more leaning towards
MIT Kerberos. We want to avoid hard to detect compatibility issues here, currently.
