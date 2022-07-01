set -e
set -x

WINRM_IMAGE="docker.software-univention.de/ucs-winrm"

pull_ucs_winrm () {
	docker pull "$WINRM_IMAGE"
}

ucs_winrm () {
	docker run --rm -v /etc/localtime:/etc/localtime:ro \
		-v "$HOME/.ucs-winrm.ini:/root/.ucs-winrm.ini:ro" "$WINRM_IMAGE" "$@"
}

# install veyon on $client
# expects veyon-*-setup.exe (software), veyon.json (config)
# and veyon-cert_*.pem (key) on the \\$server\Veyon-Installation share
install_veyon () {
	local client=$1
	local server=$2
	local local_file remote_file

	# copy files to server
	for local_file in \
		/usr/share/ucs-school-veyon-windows/*setup.exe \
		/root/veyon.json \
		"/var/lib/samba/sysvol/$(ucr get domainname)/scripts/veyon-cert_$(hostname).pem"
	do
		remote_file="$(basename "$local_file")"
		smbclient \
		        -U"Administrator%${UCS_ENV_WIN_PASSWORD}" \
		        "//$client/C\$" \
		        -c "prompt; put $local_file $remote_file"
	done

	# install veyon
	ucs_winrm run-ps --client "$client" --cmd 'C:\veyon-*-setup.exe  /S /NoMaster'
	# authkeys import always throws an error, ignore
	ucs_winrm run-ps --client "$client" --cmd "
		\$ErrorActionPreference = \"silentlycontinue\"
		cd C:\\'Program Files'\\Veyon
		.\\veyon-cli authkeys import teacher/public C:\\veyon-cert_$server.pem
	"
	# apply config
	ucs_winrm run-ps --client "$client" --cmd "
		cd C:\\'Program Files'\\Veyon
		.\\veyon-cli config import C:\\veyon.json
		.\\veyon-cli config upgrade
	"
	# reboot, just to be sure
	ucs_winrm reboot --client "$client"
}

# rename windows computer with IPto $name and
rename_and_join () {
	local ip="$1"
	local name="$2"
	local dns_server="$3"
	local domain_user="$4"
	local domain_password="$5"
	local school="$6"
	local school_group
	school_group="$(ucr get windows/domain)/Domain Users $school"

	ucs_winrm wait_for_client --client "$ip" --timeout 3600
	ucs_winrm rename-computer --timeout 3600 --name "$name" --client "$ip"
	ucs_winrm domain-join \
		--client "$ip" \
		--domainpassword "$domain_password" \
		--domainuser "$domain_user" \
		--dnsserver "$dns_server"
	# add school group to local rdp group
	# shellcheck disable=SC2016
	ucs_winrm run-ps --client "$client" --cmd '
		$computer = $env:COMPUTERNAME
		$ADSIComputer = [ADSI]("WinNT://$computer,computer")
		$auth = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-32-555")
		$local_group_name = $auth.Translate([System.Security.Principal.NTAccount]).Value.Split("\")[1]
		$local_group = $ADSIComputer.psbase.children.find($local_group_name, "Group")
		$domain_users_name = "'"$school_group"'"
		$local_group.add("WinNT://$domain_users_name")
	'
}

create_winrm_config () {
	local domain=${1:?missing domain}
	local user=${2:?missing user}
	local password=${3:?missing password}
    echo -e "[default]
domain = ${domain}
password = ${password}
user = ${user}" > "$HOME/.ucs-winrm.ini"
}

# import all clients from UCS_ENV_WINDOWS_CLIENTS into $school
import_windows_clients () {
	local school="$1"
	local type="windows" name mac ip
	local name_counter=1 import_file="/tmp/import_windows_clients.csv"
	rm -f "$import_file"
	for ip in $UCS_ENV_WINDOWS_CLIENTS; do
		# TODO, how to get the mac address?
		ping -c 4 "$ip" || true
		name="win${name_counter}"
		mac="$(arp -a| grep "($ip)" | sed 's/.*\(..:..:..:..:..:..\).*/\1/')"
		printf '%s\t%s\t%s\t%s\t%s\n' "${type}" "${name}" "${mac}" "${school}" "${ip}" >> "$import_file"
		((name_counter=name_counter+1))
	done
	# TODO Bug?
	sed -i 's/escape_dn_chars(network\.network_address)/escape_dn_chars(str(network\.network_address))/' /usr/share/ucs-school-import/scripts/import_computer
	/usr/share/ucs-school-import/scripts/import_computer "$import_file"
}

disable_wuauserv  () {
	local client="$1"
	ucs_winrm wait_for_client --client "$client" --timeout 3600
	ucs_winrm run-ps  --client "$client" --cmd '
		sc.exe config wuauserv start=disabled
		sc.exe stop wuauserv
		netsh advfirewall set allprofiles state off
		Restart-Computer -Force
    '
}

prepare_windows () {
	local pids client
	pids=()
	for client in $UCS_ENV_WINDOWS_CLIENTS; do
		disable_wuauserv "$client" &
		pids+=($!)
	done
	for pid in "${pids[@]}"; do
		wait -n "$pid"
	done
}

# uses
#  WINDOWS_CLIENTS -> list of IP's
setup_windows () {
	local domain_user="$1"
	local domain_password="$2"
	local school="$3"
	local name_counter=1 name my_ip pids
	# rename and join windows clients
	my_ip="$(ucr get interfaces/"$(ucr get interfaces/primary)"/address)"
	pids=()
	for client in $UCS_ENV_WINDOWS_CLIENTS; do
		name="win${name_counter}"
		rename_and_join "$client" "$name" "$my_ip" "$domain_user" "$domain_password" "$school" &
		pids+=($!)
		((name_counter=name_counter+1))
	done
	for pid in "${pids[@]}"; do
		wait -n "$pid"
	done
	# install and setup veyon
	pids=()
	for client in $UCS_ENV_WINDOWS_CLIENTS; do
		install_veyon "$client" "$(hostname)" &
		pids+=($!)
	done
	for pid in "${pids[@]}"; do
		wait -n "$pid"
	done
}

# call aws
aws_ec2 () {
	docker run --network host --rm -v ~/.aws:/root/.aws amazon/aws-cli ec2 "$@"
}

# get all instances with
# tag usecase:veyon-test-environment
# from subnet subnet-0c8e0b6088ba000b2
# and running
get_veyon_aws_instances () {
	local output="${1:-text}"
	local filter=()
	#filter+=("Name=tag:usecase,Values=veyon-test-environment")
	#filter+=("Name=instance-state-name,Values=running")
	filter+=("Name=network-interface.subnet-id,Values=subnet-0c8e0b6088ba000b2")
	aws_ec2 describe-instances \
		--query "Reservations[*].Instances[*].{
			name: Tags[?Key == 'Name'].Value | [0],
			ip: PrivateIpAddress,
			public_ip: PublicIpAddress,
			id: InstanceId}" \
		--filters "${filter[@]}" \
		--output "$output"
}

destroy_veyon_aws_instances () {
	get_veyon_aws_instances text | while read -r id ip name pip; do
		echo "Destroy instance $id ($name, $ip, $pip)"
		aws_ec2 terminate-instances --instance-ids "$id"
	done
}

replace_nameserver_ip_in_profile () {
	local ip=${1:?missing ip}
	local profile="/var/cache/univention-system-setup/profile"
	if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
		sed -i 's/nameserver=.*/nameserver='"$ip"'/' "$profile"
	fi
}

create_school () {
	local school=${1:?missing school}
	local server=${2:?missing server}
	/usr/share/ucs-school-import/scripts/create_ou \
		--verbose "$school" "$server" \
		--displayName="$school" \
		--sharefileserver="$server"
	/usr/share/ucs-school-import/scripts/ucs-school-testuser-import \
		--students 20 \
		--teachers 2 \
		--classes 2 \
		"$school"
}

aws_ipv6 () {
	local ipv6_address=${1:?missing ipv6}
	if [[ "$(dmidecode --string system-uuid)" == ec2* ]]; then
		# do it manually, so that we don't interfere with
		# the normal startup
		ucr set interfaces/restart/auto=false
		ucr set \
			interfaces/eth0/ipv6/default/address="$ipv6_address" \
			interfaces/eth0/ipv6/default/prefix="128"
		ip -6 addr add "$ipv6_address"/128 dev eth0
		ucr unset interfaces/restart/auto
		sleep 30
	fi
}
