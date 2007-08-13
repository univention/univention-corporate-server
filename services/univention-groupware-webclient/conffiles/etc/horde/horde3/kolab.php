<?php
$conf['cookie']['domain'] = '@%@hostname.@%@domainname@%@';
$conf['problems']['email'] = 'postmaster@@%@domainname@%@';
$conf['problems']['maildomain'] = '@%@domainame@%@';
$conf['kolab']['ldap']['basedn'] = 'dc=knut,dc=univention,dc=de';
#$conf['kolab']['ldap']['binddn'] = 'cn=manager,cn=internal,dc=knut,dc=univention,dc=de';
#$conf['kolab']['ldap']['bindpw'] = 'univention';
# $conf['kolab']['ldap']['phpdn'] = 'cn=nobody,cn=internal,dc=knut,dc=univention,dc=de';
# $conf['kolab']['ldap']['phppw'] = 'ezjq80wTLuZlBO7ZcXGdFfyLbv8BBOIsmTp11GS4';
$conf['kolab']['imap']['server'] = '@%@horde/imapserver@%@';
$conf['kolab']['imap']['maildomain'] = '@%@domainame@%@';
# $conf['kolab']['imap']['adminpw'] = 'univention';
?>
