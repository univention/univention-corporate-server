#!/usr/bin/perl -w
#
# LDAP add personal ou's from /home
# This script adds an ou for each directory in /home.
#
# Script by tarjei@nu.no.
# Remember to remove ou's like mailman, mysql, postgres, etc.

# Settings that should be changed for your setup:
$basedn = "ou=personal_addressbook, dc=example, dc=com";
$binddn = "uid=root, ou=People, dc=example, dc=com";
$passwd = "";
# End of configuration section - don't edit below here.

use Getopt::Std;
my %Options;
$user = $ARGV[0];
print "Adding ou: ou=$user,$basedn";

$FILE = "|/usr/bin/ldapadd -x $options -D '$binddn' -w $passwd";

open FILE or die;

print FILE <<EOF;
dn: ou=$user,$basedn
objectclass: top
objectClass: organizationalUnit
ou: $user

EOF
close FILE;
exit 0;
