# univention-directory-notifier
UCS - Directory Notifier

## univention-directory-notifier
UCS Directory Notifier propagates changes on the LDAP server to clients listening for them. In doing so, just the DN of the altered object is transferred. Clients that need to detect changes within an object are expected to keep a local object cache themselves to do the comparison. As of this version, the only client implementation is the UCS Directory Listener.
