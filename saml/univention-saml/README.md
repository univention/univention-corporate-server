# SAML Password change

If the user password is expired, the SAML login dialog offers a password changing functionality.
This changes the password via curl against the UMC-Server, which uses pam-krb5, to change the password.
pam-krb5 changes the Password in Samba (if Samba is installed) and not in Open-LDAP.
The S4-Connector syncs the password hashes back to Open-LDAP. This results in a race condition.
If the S4-Connector is too slow or not running, the Login Dialog is shown again asking to re-login after the password changed instead of being logged in immediately.
This may also fail, if one is faster to re-type the new credentials than the S4-Connector.

→ We should change the Samba-4 Heimdal server with the same patches we have for Debians Heimdal, so the Password is changed in Open-LDAP via UDM.
