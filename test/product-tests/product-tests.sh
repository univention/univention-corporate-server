#!/bin/bash

password=univention
user=root
helpmsg=false
while getopts ":p:s:u:t:h" opt; do
	case $opt in
		s)
			server=$OPTARG
			;;
		p)
			password=$OPTARG
			;;
		u)
			user=$OPTARG
			;;
		t)
			product_test=$OPTARG
			;;
		h)
			helpmsg=true
			;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			;;
		:)
			echo "Option -$OPTARG requires an argument." >&2
			exit 1
      ;;
	esac
done

if $helpmsg; then
	echo "usage: $0 -t test [-s SERVER_IP -p PASSWORD -u USER]"
	exit 0
fi

if [ ! -f "$product_test" ]; then
	echo "ERROR: no test given" >&2
	exit 1
fi

set -e

section=$(dirname "$product_test")

if [ -n "$server" ]; then
	sshpass -p "$password" scp -r "$section" "$user"@"$server":/root
	if [ -f "$product_test.environment" ]; then
		sshpass -p "$password" scp "$product_test.environment" "$user"@"$server":/root/.ssh/environment
		sshpass -p "$password" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -T "$user"@"$server" 1>/dev/null <<EOF
ucr set sshd/PermitUserEnvironment=yes
ucr set sshd/config/PermitUserEnvironment=yes
echo "PermitUserEnvironment yes" >> /etc/ssh/sshd_config
echo "sleep 1; service ssh restart" | at now
EOF
		sleep 3
	fi
	sshpass -p "$password" scp -r "./ucs-ec2-tools/shared-utils" "$user"@"$server":/root
	sshpass -p "$password" scp -r "./utils/"* "$user"@"$server":/root
	sshpass -p "$password" scp -r "./product-tests" "$user"@"$server":/root
	sshpass -p "$password" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -T "$user"@"$server" <<EOF
cd /root
bash -x $product_test
env
EOF
else
	bash -x $product_test
fi
