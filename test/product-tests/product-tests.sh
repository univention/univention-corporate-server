#!/bin/bash

password=univention
user=root
while getopts ":p:s:u:t:" opt; do
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
		\?)
			echo "Invalid option: -$OPTARG" >&2
			;;
		:)
			echo "Option -$OPTARG requires an argument." >&2
			exit 1
      ;;
	esac
done

test -f "$product_test" || (echo "ERROR: no test given" >&2; exit 1)

set -e
set -x

section=$(dirname "$product_test")

if [ -n "$server" ]; then
	sshpass -p "$password" scp -r "$section" "$user"@"$server":/root
	test -f "$product_test.environment" && sshpass -p "$password" scp "$product_test.environment" "$user"@"$server":/root/environment
	sshpass -p "$password" scp -r "../ucs-ec2-tools/shared-utils" "$user"@"$server":/root
	sshpass -p "$password" scp -r "../utils/"* "$user"@"$server":/root
	sshpass -p "$password" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -T "$user"@"$server" <<EOF
cd /root
bash -x $product_test
EOF
else
	bash -x $product_test
fi
