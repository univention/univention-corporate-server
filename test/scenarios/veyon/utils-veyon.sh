set -e

WINRM_IMAGE="docker.software-univention.de/ucs-winrm"

pull_ucs_winrm () {
	docker pull "$WINRM_IMAGE"
}

ucs-winrm () {
	docker run --rm -v /etc/localtime:/etc/localtime:ro \
		-v "$HOME/.ucs-winrm.ini:/root/.ucs-winrm.ini:ro" "$WINRM_IMAGE" "$@"
}

# install veyon on $client
# expects veyon-*-setup.exe (software), veyon.json (config)
# and veyon-cert_*.pem (key) on the \\$server\Veyon-Installation share
install_veyon () {
	local client=$1
	local server=$2
	# copy setup and config file and key
	ucs-winrm run-ps --credssp --client "$client" --cmd "
		New-PSDrive -Name R -PSProvider FileSystem -Root \\\\$server\Veyon-Installation
		Copy-Item R:\\veyon-*-setup.exe -Destination C:\\
		Copy-Item R:\\veyon.json -Destination C:\\
		Copy-Item R:\\veyon-cert_*.pem C:\\
	"
	# install veyon
	ucs-winrm run-ps --client "$client" --cmd 'C:\veyon-*-setup.exe  /S /NoMaster'
	# authkeys import always throws an error, ignore
	ucs-winrm run-ps --credssp --client "$client" --cmd "
		\$ErrorActionPreference = \"silentlycontinue\"
		cd C:\\'Program Files'\\Veyon
		.\\veyon-cli authkeys import teacher/public C:\\veyon-cert_$server.pem
	"
	# apply config
	ucs-winrm run-ps --credssp --client "$client" --cmd "
		cd C:\\'Program Files'\\Veyon
		.\\veyon-cli config import C:\\veyon.json
		.\\veyon-cli config upgrade
	"
	# reboot, just to be sure
	ucs-winrm reboot --client "$client"
}

# rename windows computer with IPto $name and
rename_and_join () {
	local ip="$1"
	local name="$2"
	local dns_server="$3"
	local domain_user="$4"
	local domain_password="$5"
	ucs-winrm rename-computer --name "$name" --client "$ip"
	ucs-winrm domain-join \
		--client "$ip" \
		--domainpassword "$domain_password" \
		--domainuser "$domain_user" \
		--dnsserver "$dns_server"
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
		ping -c 4 "$ip"
		name="win${name_counter}"
		mac="$(arp -a| grep "$ip" | sed 's/.*\(..:..:..:..:..:..\).*/\1/')"
		printf '%s\t%s\t%s\t%s\t%s\n' "${type}" "${name}" "${mac}" "${school}" "${ip}" >> "$import_file"
		((name_counter=name_counter+1))
	done
	# TODO Bug?
	sed -i 's/escape_dn_chars(network\.network_address)/escape_dn_chars(str(network\.network_address))/' /usr/share/ucs-school-import/scripts/import_computer
	/usr/share/ucs-school-import/scripts/import_computer "$import_file"
}

# uses
#  WINDOWS_CLIENTS -> list of IP's
setup_windows () {
	local domain_user="$1"
	local domain_password="$2"
	local name_counter=1 name my_ip pids
	# setup veyon key and config
	cp "/var/lib/samba/sysvol/$(ucr get domainname)/scripts/veyon-cert_$(hostname).pem" /usr/share/ucs-school-veyon-windows/
	cp /root/veyon.json /usr/share/ucs-school-veyon-windows/
	# rename and join windows clients
	my_ip="$(ucr get interfaces/"$(ucr get interfaces/primary)"/address)"
	pids=()
	for client in $UCS_ENV_WINDOWS_CLIENTS; do
		name="win${name_counter}"
		rename_and_join "$client" "$name" "$my_ip" "$domain_user" "$domain_password" &
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

get_veyon_aws_instances () {
	local output=${1:=text}
	aws_ec2 describe-instances \
		--query "Reservations[*].Instances[*].{name: Tags[?Key == 'Name'].Value | [0], ip: PrivateIpAddress, public_ip: PublicIpAddress, id: InstanceId }" \
		--filters "Name=tag:usecase,Values=veyon-test-environment" \
		--output "$output"
}
