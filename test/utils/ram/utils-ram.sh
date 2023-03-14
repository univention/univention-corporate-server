# shellcheck shell=sh
set -e
set -x

udm_rest_setup () {
	ucr set directory/manager/rest/processes=0
	systemctl restart univention-directory-manager-rest
}

kelvin_setup () {
	univention-app configure ucsschool-kelvin-rest-api --set ucsschool/kelvin/processes=0 --set ucsschool/kelvin/log_level=DEBUG && univention-app restart ucsschool-kelvin-rest-api
}

set_udm_properties_for_kelvin () {
	cat <<EOT > /etc/ucsschool/kelvin/mapped_udm_properties.json
{
		"user": [
				"accountActivationDate",
				"displayName",
				"divisNameAffix",
				"divisNickname",
				"e-mail",
				"networkAccess",
				"PasswordRecoveryEmail",
				"PasswordRecoveryEmailVerified",
				"pwdChangeNextLogin",
				"serviceprovider",
				"ucsschoolPurgeTimestamp",
				"uidNumber"
		],
		"school_class": [
				"divis_startdate",
				"divis_enddate",
				"divis_classtype",
				"idi_schoolyear",
				"group_source-id",
				"isIServGroup",
				"isLMSGroup",
				"disabled",
				"divis_coursetype",
				"recordUID",
				"idi_schoolyear",
				"purgeDate",
				"serviceprovidergroup"
		],
		"workgroup": [
				"divis_startdate",
				"divis_enddate",
				"divis_classtype",
				"idi_schoolyear",
				"group_source-id",
				"isIServGroup",
				"isLMSGroup",
				"disabled",
				"divis_coursetype",
				"recordUID",
				"idi_schoolyear",
				"purgeDate",
				"serviceprovidergroup"
		],
		"school": [
				"description",
				"dwh_ShortName"
		]
}

EOT
	echo "{}" > /var/lib/ucs-school-import/configs/kelvin.json
	cat /var/lib/ucs-school-import/configs/kelvin.json
	univention-install -y jq moreutils # we need `jq` and `sponge`
	jq '. += {
		"scheme":
			{
				"username":
					{
						"default": "<lastname:umlauts>[0:4]<firstname:umlauts>[0:4]<:lower>[COUNTER2]"
					},
				"email": "<firstname:umlauts>.<lastname:umlauts><:lower>[COUNTER2]@<school>.<maildomain>"
			},
		"maildomain": "hamburg.de"
	}' /var/lib/ucs-school-import/configs/kelvin.json | sponge /var/lib/ucs-school-import/configs/kelvin.json
	udm mail/domain create --ignore_exists --set name=dwh-shortname-testschool.hamburg.de --position "cn=domain,cn=mail,$(ucr get ldap/base)"
	udm mail/domain create --ignore_exists --set name=dwh-shortname-testschool2.hamburg.de --position "cn=domain,cn=mail,$(ucr get ldap/base)"

	cat <<EOT > /var/lib/ucs-school-import/kelvin-hooks/bsb_school_dwh_short_name.py
from typing import Any, Dict

from ldap.filter import escape_filter_chars
from ucsschool.importer.exceptions import InitialisationError, UnknownSchoolName
from ucsschool.importer.utils.format_pyhook import FormatPyHook


UDM_PROPERTY_NAME = "dwh_ShortName"


def escape_filter_chars_exc_asterisk(value: str) -> str:
	value = escape_filter_chars(value)
	value = value.replace(r"\2a", "*")
	return value


class BsbSchoolDwhShortName(FormatPyHook):
	"""
	Format hook that will modify the 'school' attribute of a user during the creation of an 'email'
	address from a schema.
	The value that will replace the original 'school' value is taken from the extended attribute
	'dwh_ShortName' (constant 'UDM_PROPERTY_NAME') of the users primary school.
	Use this hook in combination with a configuration like this:
	{
	  "maildomain": "hamburg.de",
	  "scheme": {
		"email": "<firstname:umlauts>.<lastname:umlauts><:lower>[COUNTER2]@<school>.<maildomain>"
	  }
	}
	"""
	priority = {
		"patch_fields_staff": 10,
		"patch_fields_student": 10,
		"patch_fields_teacher": 10,
		"patch_fields_teacher_and_staff": 10,
	}
	properties = ("email",)
	_dwh_short_name: Dict[str, str] = {}

	def __init__(self, *args, **kwargs):
		"""Retrieve all OU names in one query. Much more efficient than in hundreds of queries."""
		super().__init__(*args, **kwargs)
		self.logger.info("Looking for extended attribute %r...", UDM_PROPERTY_NAME)
		self.ldap_attr = self.ldap_attribute_of_extended_udm_property(UDM_PROPERTY_NAME)
		self.logger.info("LDAP attribute is %r.", self.ldap_attr)
		self.logger.info("Caching %r values of all schools...", self.ldap_attr)
		all_dwh_short_names = self.retrieve_school_dwh_short_names("*")
		for ou, dwh_short_name in all_dwh_short_names.items():
			self._dwh_short_name[ou.lower()] = dwh_short_name
		self.logger.info("Retrieved %r names from LDAP.", len(self._dwh_short_name))

	def ldap_attribute_of_extended_udm_property(self, udm_property_name: str) -> str:
		filter_s = f"(&(univentionObjectType=settings/extended_attribute)(cn={udm_property_name}))"
		query_res = self.lo.search(filter_s, attr=["univentionUDMPropertyLdapMapping"])
		if not query_res:
			raise InitialisationError(f"Unknown extended attribute {udm_property_name!r}.")
		_, attrs = query_res[0]
		return attrs["univentionUDMPropertyLdapMapping"][0].decode("UTF-8")

	def retrieve_school_dwh_short_names(self, ou_filter: str) -> Dict[str, str]:
		ou_filter_escaped = escape_filter_chars_exc_asterisk(ou_filter)
		filter_s = f"(&(objectClass=ucsschoolOrganizationalUnit)(ou={ou_filter_escaped}))"
		query_res = self.lo.search(filter_s, attr=[self.ldap_attr, "ou"])
		if not query_res:
			raise UnknownSchoolName(f"Unknown school {ou_filter!r} (filter: {filter_s!r}).")
		res = {}
		for dn, attrs in query_res:
			ou = attrs["ou"][0].decode("UTF-8")
			dwh_short_name = attrs.get(self.ldap_attr, [])
			if dwh_short_name:
				res[ou.lower()] = dwh_short_name[0].decode("UTF-8")
			else:
				self.logger.warning("Empty 'dwh_ShortName' value for school %r. Using %r.", ou, ou)
				res[ou.lower()] = ou
		return res

	def school_dwh_short_name(self, school: str) -> str:
		ou = school.lower()
		if ou not in self._dwh_short_name:
			self._dwh_short_name[ou] = self.retrieve_school_dwh_short_names(school)[ou]
		return self._dwh_short_name[ou]

	def patch_school_field(self, property_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
		if property_name == "email":
			fields["school"] = self.school_dwh_short_name(fields["school"])
		return fields

	patch_fields_staff = patch_school_field
	patch_fields_student = patch_school_field
	patch_fields_teacher = patch_school_field
	patch_fields_teacher_and_staff = patch_school_field

EOT

	univention-app shell ucsschool-kelvin-rest-api /var/lib/univention-appcenter/apps/ucsschool-kelvin-rest-api/data/update_openapi_client
	univention-app restart ucsschool-kelvin-rest-api
}

install_frontend_app () {
	local app="$1"
	local main_image="$2"
	local branch_image="$3"
	univention-install --yes univention-appcenter-dev
	if [ -n "$branch_image" ]; then
		univention-app dev-set "$app" "DockerImage=$branch_image"
	else
		if [ "$UCSSCHOOL_RELEASE" = "scope" ]; then
			univention-app dev-set "$app" "DockerImage=$main_image"
		fi
	fi
	univention-app install "$app" --noninteractive --username Administrator --pwdfile /tmp/univention --set log_level=DEBUG --set kelvin_timeout=120
	commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$(ucr get "appcenter/apps/$app/container")")
	echo "Docker image built from commit: $commit"
}

install_frontend_apps () {
	echo -n univention > /tmp/univention

	install_frontend_app "ucsschool-bff-users" "gitregistry.knut.univention.de/univention/ucsschool-components/ui-users:latest" "$UCS_ENV_RANKINE_USERS_IMAGE"
	install_frontend_app "ucsschool-bff-groups" "gitregistry.knut.univention.de/univention/ucsschool-components/ui-groups:latest" "$UCS_ENV_RANKINE_GROUPS_IMAGE"

	docker images
	docker ps -a
}

enabled_internal_school_repo () {
	# also add internal school repo for up-to-date frontend packages
	local version
	if [ "$UCSSCHOOL_RELEASE" != "public" ]; then
		version="${UCS_VERSION%%-*}"
		cat <<EOF > "/etc/apt/sources.list.d/99_internal_school.list"
deb [trusted=yes] http://192.168.0.10/build2/ ucs_$version-0-ucs-school-$version/all/
deb [trusted=yes] http://192.168.0.10/build2/ ucs_$version-0-ucs-school-$version/\$(ARCH)/
EOF
	fi
}

disable_internal_school_repo () {
	rm -f /etc/apt/sources.list.d/99_internal_school.list
}

install_ui_common () {
	enabled_internal_school_repo
	univention-install -y ucs-school-ui-common
	disable_internal_school_repo
}

install_frontend_packages () {
	enabled_internal_school_repo
	univention-install -y ucs-school-ui-users-frontend
	univention-install -y ucs-school-ui-groups-frontend
	disable_internal_school_repo
}

create_test_oidc_clients () {
	# create dev clients for easier testing
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-users-dev --direct-access
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-groups-dev --direct-access
}

enable_bsb_repos () {
	# get APT customer repo $username and @password from the RAM secrets
	# shellcheck disable=SC2046
	export $(grep -v '^#' /etc/ram.secrets| xargs)
	echo -n univention > /tmp/univention

	# shellcheck disable=SC2154
	/usr/sbin/univention-config-registry set \
		repository/online/component/fhh-bsb-iam=yes \
		repository/online/component/fhh-bsb-iam/server='service.knut.univention.de' \
		repository/online/component/fhh-bsb-iam/prefix="apt/$username" \
		repository/online/component/fhh-bsb-iam/parts='maintained' \
		repository/online/component/fhh-bsb-iam/username="$username" \
		repository/online/component/fhh-bsb-iam/password="$password"

	# also add internal repo
	echo "enabling repository ucs_5.0-0-${BSB_PACKAGE_SCOPES:-fhh-bsb-iam-dev-intern}..."
	cat <<EOF > /etc/apt/sources.list.d/99_bsb.list
deb [trusted=yes] http://192.168.0.10/build2/ ucs_5.0-0-${BSB_PACKAGE_SCOPES:-fhh-bsb-iam-dev-intern}/all/
deb [trusted=yes] http://192.168.0.10/build2/ ucs_5.0-0-${BSB_PACKAGE_SCOPES:-fhh-bsb-iam-dev-intern}/\$(ARCH)/
EOF
}

install_all_attributes_primary () {
	enable_bsb_repos
	univention-install -y \
		ucsschool-iserv-custom-ldap-extension \
		ucsschool-divis-custom-ldap-extension \
		ucsschool-moodle-custom-ldap-extension \
		univention-saml
	systemctl restart univention-directory-manager-rest.service
}

install_bsb_m2 () {
	# install the bsb milestone 2 metapackage
	enable_bsb_repos
	/usr/sbin/univention-config-registry set dataport/umgebung='DEV'

	univention-install -y bsb-release-m2
	systemctl restart univention-directory-manager-rest.service
}

install_bsb_packages () {
	enable_bsb_repos
	/usr/sbin/univention-config-registry set dataport/umgebung='DEV'

	univention-install -y \
		bsb-release-m1 \
		bsb-release-m2 \
		bsb-release-m3 \
		ucsschool-divis-custom-import-config \
		ucs-school-umc-multiple-users-export \
		ucs-school-umc-wizards \
		univention-management-console-module-custom-grouppermissions \
		univention-self-service

	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		univention-run-join-scripts --force --run-scripts 35ucs-school-umc-multiple-users-export.inst
	fi
	echo "rdate -n 192.168.0.3" >> "$HOME/.profile"

	systemctl restart univention-directory-manager-rest.service
}

create_test_admin_account () {
	local username password fqdn token
	local technical_admin_pw="${1:-univention}"
	test -z "$(which jq)" && univention-install -y jq
	test -z "$(which curl)" && univention-install -y curl
	username="Administrator"
	password="univention"
	fqdn="$(hostname -f)"
	token="$(curl -s -k -X POST "https://$fqdn/ucsschool/kelvin/token" \
		-H "Content-Type:application/x-www-form-urlencoded" \
		-d "username=$username" \
		-d "password=$password" | jq -r '.access_token')"
	udm mail/domain create --ignore_exists --set name=school1.hamburg.de --position "cn=domain,cn=mail,$(ucr get ldap/base)"
	sleep 10 # wait for replication?
	univention-app restart ucsschool-kelvin-rest-api
	echo "Waiting for Kelvin to restart"
	until $(curl --output /dev/null --silent --head --fail "https://$fqdn/ucsschool/kelvin/v1/openapi.json"); do
		printf '.'
		sleep 1
	done
	sleep 10 #just in case
	curl --fail -X POST "https://$fqdn/ucsschool/kelvin/v1/users/" \
		-H "Authorization: Bearer $token" \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d '{
			"name": "admin",
			"firstname": "test",
			"lastname": "admin",
			"password": "A1.univentionunivention",
			"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/school1",
			"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/teacher"],
			"record_uid": "admin",
			"ucsschool_roles": ["technical_admin:bsb:*", "teacher:school:school1"]
		}'
	udm users/user modify \
		--dn "uid=admin,cn=lehrer,cn=users,ou=school1,$(ucr get ldap/base)" \
		--set password="$technical_admin_pw" \
		--append groups="cn=Domain Users,cn=groups,$(ucr get ldap/base)"
}

create_bsb_test_users () {
	fqdn="$(hostname -f)"
	# create fl user
	create_user_from_json '{
		"name": "fl-thawkins",
		"firstname": "Taylor",
		"lastname": "Hawkins",
		"password": "!Univention2023",
		"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/5048",
		"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/school_admin"],
		"record_uid": "1a23bc45-67890-1234-56d7-89012345e6f7g",
		"ucsschool_roles": ["technical_admin:bsb:*", "teacher:school:0000Schuldock"]
	}'
	# create schuladmin
	create_user_from_json '{
		"firstname": "Jeff",
		"lastname": "Buckley",
		"password": "!Univention2023",
		"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/5048",
		"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/school_admin"],
		"record_uid": "027ada41-60dc-47fd-96dc-98559ae65245",
		"ucsschool_roles": ["school_admin:bsb:5048", "school_admin:school:5048"]
	}'
	# create lehrkraft
	create_user_from_json '{
		"firstname": "Layne",
		"lastname": "Staley",
		"password": "!Univention2023",
		"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/5048",
		"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/teacher"],
		"record_uid": "ee4ba50b-ef8b-483f-8a06-0aa8e7dac374",
		"ucsschool_roles": ["teacher:bsb:5048", "teacher:school:5048"]
	}'
	# create nutzende
	create_user_from_json '{
		"firstname": "Janis",
		"lastname": "Joplin",
		"password": "!Univention2023",
		"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/5048",
		"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/student"],
		"record_uid": "67a693e9-a080-4a84-aec6-46f6a0b68a1f",
		"ucsschool_roles": ["generic_user:bsb:5048", "student:school:5048"]
	}'
	# create lernende
	create_user_from_json '{
		"firstname": "Amy",
		"lastname": "Winehouse",
		"password": "!Univention2023",
		"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/5048",
		"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/student"],
		"record_uid": "195687c7-99c5-47b6-9ff0-42290683fe8a",
		"ucsschool_roles": ["student:bsb:5048", "student:school:5048"]
	}'
}

create_user_from_json () {
	local username password fqdn token
	test -z "$(which jq)" && univention-install -y jq
	test -z "$(which curl)" && univention-install -y curl
	username="Administrator"
	password="univention"
	fqdn="$(hostname -f)"
	token="$(curl -s -k -X POST "https://$fqdn/ucsschool/kelvin/token" \
		-H "Content-Type:application/x-www-form-urlencoded" \
		-d "username=$username" \
		-d "password=$password" | jq -r '.access_token')"
	curl --fail -X POST "https://$fqdn/ucsschool/kelvin/v1/users/" \
		-H "Authorization: Bearer $token" \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d "$1"
}

create_school_ou () {
	# $1: displayname $2: ou $3: edu-dc
	test -e "/usr/share/ucs-school-import/scripts/create_ou" || exit 1
	/usr/share/ucs-school-import/scripts/create_ou --displayName "$1" -v "$2" "$3"
	udm container/ou modify --dn "ou=$2,$(ucr get ldap/base)" --set dwh_ShortName="$3" --set description="$3"
}

load_balancer_setup () {
	local extra_config="/var/loadbalance.conf"
	a2enmod lbmethod_byrequests || return 1
	cat <<EOF > "$extra_config"
<Proxy "balancer://bff">
$(
	for ip in "$@"; do
		echo "BalancerMember \"http://$ip/ucsschool\""
	done
)
</Proxy>
ProxyPass		 "/ucsschool" "balancer://bff"
ProxyPassReverse "/ucsschool" "balancer://bff"
EOF
	univention-add-vhost --conffile "$extra_config" "loadbalancer.$(ucr get hostname).$(ucr get domainname)" 443 || return 1
	systemctl start apache2 || return 1
}

load_balancer_setup_haproxy () {
	# ha proxy seems to be much faster and more reliable
	ucr set security/packetfilter/package/univention-apache/tcp/9443/all='ACCEPT'
	service univention-firewall restart
	# ha proxy needs the privat key
	cat "/etc/univention/ssl/primary.$(ucr get domainname)/private.key" >> "/etc/univention/ssl/primary.$(ucr get domainname)/cert.pem"
	univention-install -y haproxy
	cat <<EOF >> "/etc/haproxy/haproxy.cfg"
frontend sample_httpd
	bind :9443 ssl crt /etc/univention/ssl/primary.school.test/cert.pem
	default_backend bffs

backend bffs
	balance roundrobin
	timeout server 100000
$(
	for host in "$@"; do
		echo -e "\tserver $host $host.$(ucr get domainname):443 ssl ca-file /etc/ssl/certs/ca-certificates.crt"
	done
)
EOF
	service haproxy restart
}

performance_test_settings () {
	ucr set \
		nss/group/cachefile/invalidate_on_changes=no \
		listener/module/portal_groups/deactivate=yes
	service univention-directory-listener restart
}

performance_test_setup () {
	ucr set security/limits/user/root/soft/nofile=10240
	ucr set security/limits/user/root/hard/nofile=10240
	echo "fs.file-max=1048576" > /etc/sysctl.d/99-file-max.conf
	sysctl -p
}

create_mail_domains_dwh_ShortName () {
	DOM="$(jq -r .maildomain /var/lib/ucs-school-import/configs/kelvin.json)"
	for dwh_ShortName in $(udm container/ou list | grep dwh_ShortName: | cut -d ' ' -f 4); do
		if [ "$dwh_ShortName" = "None" ]; then
			continue
		fi
		udm mail/domain create --position "cn=domain,cn=mail,$(ucr get ldap/base)" --ignore_exists --set name="$dwh_ShortName.$DOM"
	done
}

create_mail_domains () {
	DOM="$(jq -r .maildomain /var/lib/ucs-school-import/configs/kelvin.json)"
	for OU in $(udm container/ou list | grep name: | cut -d ' ' -f 4); do
		udm mail/domain create --position "cn=domain,cn=mail,$(ucr get ldap/base)" --ignore_exists --set name="$OU.$DOM"
	done
}

SAR_ARGS=( -b -n DEV,IP,TCP,UDP -P ALL -q -r ALL -S -u ALL )
DATA_DIR=/var/log/perfstats

start_system_stats_collection () {
 local host="${1:?missing hostname}"

 apt-get install -y scour sysstat
 mkdir -pv "$DATA_DIR"
 touch "$DATA_DIR/empty-$host"
 # Starting the next two commands in the background has proven to be unreliable. Retrying in a loop.
 count=0; while ! pgrep -f 'ram.sar' > /dev/null && test $count -lt 100; do (nohup sar "${SAR_ARGS[@]}" -o "$DATA_DIR/ram.sar" 1 >/dev/null &); count=$(( count + 1 )); sleep 1; done
 # When not looked at every day anymore, reduce size with: ... | bzip2 -9c > $DATA_DIR/stats-$host.top.txt.bz2 &
 count=0; while ! pgrep -f 'top -bci' > /dev/null && test $count -lt 100; do (nohup top -bci -w512 -d 1 > "$DATA_DIR/stats-$host.top.txt" &); count=$(( count + 1 )); sleep 1; done
 pgrep -af 'top|sar'
}

end_system_stats_collection () {
 local host="${1:?missing hostname}"

 pgrep -af 'top|sar'
 pkill -f ram.sar -SIGINT || true
 pkill -f 'top -bci' || true
 ls -la "$DATA_DIR"
 [ -e "$DATA_DIR/ram.sar" ] && sadf -g "$DATA_DIR/ram.sar" -- "${SAR_ARGS[@]}" | scour -o "$DATA_DIR/stats-$host.sar.svg" || echo "Not found: $DATA_DIR/ram.sar"
 # stats.sar.txt (decompressed) can be uploaded to https://sarchart.dotsuresh.com/ for interactive graphs
 [ -e "$DATA_DIR/ram.sar" ] && sar "${SAR_ARGS[@]}" -f "$DATA_DIR/ram.sar" | bzip2 -9c > "$DATA_DIR/stats-$host.sar.txt.bz2" || echo "Not found: $DATA_DIR/ram.sar"
}

umc_saml_session_workaround () {
	# see https://git.knut.univention.de/univention/ucsschool-components/ui-users/-/issues/248
	ucr set umc/saml/assertion-lifetime="$((8 * 60 * 60))"ucr set umc/saml/assertion-lifetime="$((8 * 60 * 60))"
	/usr/share/univention-management-console/saml/update_metadata
}
