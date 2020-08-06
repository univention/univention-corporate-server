#!/bin/bash
univention-ldapsearch "(&(objectclass=univentionDomainController)(univentionService=Samba 4))" cn | sed -n 's/^cn: \(.*\)/\1/p'
univention-ldapsearch "uid=Administrator" | ldapsearch-wrapper
declare -a args=()
args[${#args[@]}]="-D"
cat /etc/fstab | grep '^[^#]'
univention-ldapsearch -o ldif-wrap=no '(uid=Administrator)' 1.1 | grep ^dn | sed -ne 's/^dn: //p'
sed -rne 's|^dn: (.*)$|\1|p' </dev/null
cat /etc/fstab /etc/fstab | sort -u
echo "$(date)"
echo "$(date): Message"
ldapsearch -x -LLLo ldif-wrap=no -U "$(ucr get ldap/hostdn)" -w "$(cat /etc/machine.secret)" -b "$(ucr get ldap/base)" -s base 1.1 || die
memtotal=$(more /proc/meminfo | grep ^MemTotal: | awk {'print $2'})
echo "$(date)"  # ucslint
echo "$(date)"  # ucslint: 0017-10
