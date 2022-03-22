#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from configparser import ConfigParser

template_file = "scenarios/autotest-247-ucsschool-id-broker.cfg"

config = ConfigParser(interpolation=None)
config.read(template_file)
sections = config.sections()
sections.remove("Global")
recover_command = config.getint("Global", "recover")
new_recover_command = recover_command + 1
config.set("Global", "recover", str(new_recover_command))

for section in sections:
    template_name = section
    if not template_name.startswith("IDBroker-"):
        template_name = "IDBroker-{section}".format(section=section)
    config.set(
        section,
        "command{recover_command}".format(recover_command=recover_command),
        """
ucr set internal/kvm/template/old/ip="$(ucr get interfaces/eth0/address)"
echo -e "version=@%@version/version@%@-@%@version/patchlevel@%@-$(date +%Y-%m-%d)\\nversion_version=@%@version/version@%@" | ucr filter>/tmp/ucs.ver
GET /tmp/ucs.ver ucs.ver
. base_appliance.sh && appliance_poweroff
SSH_DISCONNECT
LOCAL sleep 60
SOURCE ucs.ver
SERVER ucs-kt-put -C single -O Others -c "[{section}_KVM_NAME]" "[version]_{template_name}_amd64" --remove-old-templates='[version_version]-*_{template_name}_amd64.tar.gz' --keep-last-templates=1
""".format(section=section, template_name=template_name),
    )
    config.set(section, "command{new_recover_command}".format(new_recover_command=new_recover_command), "")

# add jump host for ldap modifications
new_section = "JumpHost"
config.add_section(new_section)
config.set(new_section, "kvm_template", "[ENV:KVM_TEMPLATE]")
config.set(new_section, "kvm_ucsversion", "[ENV:KVM_UCSVERSION]")
for i in range(1, recover_command):
    config.set(new_section, "command{i}".format(i=i), "")
config.set(new_section, "command{recover_command}".format(recover_command=recover_command - 1), """
. utils.sh && basic_setup
. utils.sh && rotate_logfiles
. utils.sh && activate_idbroker_devel_scope
#
. utils-school-idbroker.sh && add_to_hosts "[Traeger1_IP]" "traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[Traeger2_IP]" "traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Primary_IP]" "idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Provisioning_IP]" "provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Self-Disclosure_IP]" "self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-keycloak_IP]" "kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN] login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_TRAEGER1_FQDN=traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_TRAEGER2_FQDN=traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_SELF_DISCLOSURE_FQDN=self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_PROVISIONING_FQDN=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_KEYCLOAK_FQDN=login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_BROKER_LDAPS=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN] self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN] idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN] kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_ANSIBLE_SSH_USER=root"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_ANSIBLE_SSH_PRIVATE_KEY=/root/.ssh/tech.pem"
#
# create ssh config and prepare ldap server
#
. utils-school-idbroker.sh && prepare_jump_host
cd /var/lib/id-broker-performance-tests/prepare_ldap && ./prepare_ldap.sh
""")
config.set(new_section, "command{recover_command}".format(recover_command=recover_command), "")
config.set(new_section, "command{new_recover_command}".format(new_recover_command=new_recover_command), "")
# add files
config.set(new_section, "files", """utils/utils-school-idbroker.sh /root/
~/ec2/keys/tech.pem /root/.ssh/
""")


config.write(sys.stdout)
