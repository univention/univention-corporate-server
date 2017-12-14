# univention-directory-logger
UCS - Directory Logger

## univention-directory-logger
UCS Directory Logger is a module for the UCS Directory Listener that logs changes to the UCS LDAP Directory as protocol records to a log file. Each record reports the timestamp and kind of the modification along with the authentification ID (LDAP DN) of the initiator of a modification. The changed attributes are reported as well. Each record contains the hash value of the previous record to build up a chain of trusted records. The hash value of each new generated record is sent to the syslog where it may be directed to remote hosts to allow independent auditing.
