#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from configparser import ConfigParser


template_file = "scenarios/autotest-247-ucsschool-id-broker.cfg"

config = ConfigParser(interpolation=None)
config.read(template_file)
sections = config.sections()
sections.remove("Global")
recover_command = config.getint("Global", "recover",)
kvm_extra_label = config.get("Global", "kvm_extra_label",)
config.set("Global", "kvm_extra_label", f"{kvm_extra_label}-kvm-templates",)
new_recover_command = recover_command + 2
config.set("Global", "recover", str(new_recover_command),)
config.set("Global", "kvm_memory", "8G",)

for section in sections:
    template_name = section
    if not template_name.startswith("IDBroker-"):
        template_name = f"IDBroker-{section}"
    config.set(
        section,
        f"command{recover_command}",
        """
. utils-school-idbroker.sh && load_sddb_jenkins
""",)
    config.set(
        section,
        f"command{recover_command + 1}",
        """
rm -f /root/.ssh/environment
ucr set internal/kvm/template/old/ip="$(ucr get interfaces/eth0/address)"
apt-get -y remove firefox-esr
apt-get clean
echo -e "version=@%@version/version@%@-@%@version/patchlevel@%@-$(date +%Y-%m-%d)\\nversion_version=@%@version/version@%@" | ucr filter>/tmp/ucs.ver
GET /tmp/ucs.ver ucs_[SELF].ver
. base_appliance.sh && appliance_poweroff
SSH_DISCONNECT
SERVER id=$(virsh domid SELF_KVM_NAME) && [ -n "${{id#-}}" ] && virsh event --domain "$id" --event lifecycle --timeout 120 --timestamp || :
SOURCE ucs_[SELF].ver
SERVER ucs-kt-put -C single -O Others -c "[SELF_KVM_NAME]" "[version]_{template_name}_amd64" --remove-old-templates='[version_version]-*_{template_name}_amd64.tar.gz' --keep-last-templates=1
LOCAL rm -f ucs_[SELF].ver
""".format(template_name=template_name),)
    config.set(section, f"command{new_recover_command}", "",)

# add jump host for ldap modifications
new_section = "JumpHost"
config.add_section(new_section)
config.set(new_section, "kvm_template", "[ENV:KVM_TEMPLATE]",)
config.set(new_section, "kvm_ucsversion", "[ENV:KVM_UCSVERSION]",)
for i in range(1, recover_command,):
    config.set(new_section, f"command{i}", "",)
config.set(new_section, f"command{recover_command - 1}", """
. utils.sh && basic_setup
. utils.sh && rotate_logfiles
. utils.sh && activate_idbroker_devel_scope
#
. utils-school-idbroker.sh && add_to_hosts "[Traeger1_IP]" "traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[Traeger2_IP]" "traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Primary_IP]" "idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Provisioning_IP]" "provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-Self-Disclosure_IP]" "self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-keycloak1_IP]" "kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN] login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-keycloak2_IP]" "kc2.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[IDBroker-sddb_IP]" "sddb.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_TRAEGER1_FQDN=traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_TRAEGER2_FQDN=traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_SELF_DISCLOSURE_FQDN=self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_PROVISIONING_FQDN=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_KEYCLOAK_FQDN=login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_BROKER_LDAPS=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN] self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN] idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN] kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN] kc2.[ENV:UCS_ENV_IDBROKER_DOMAIN] sddb.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_ANSIBLE_SSH_USER=root"
. utils-school-idbroker.sh && add_to_ssh_environment "UCS_ENV_ANSIBLE_SSH_PRIVATE_KEY=/root/.ssh/tech.pem"
#
# create ssh config and prepare ldap server
#
. utils-school-idbroker.sh && prepare_jump_host
/var/lib/id-broker-performance-tests/prepare_ldap/prepare_ldap.sh
""",)
config.set(new_section, f"command{recover_command}", "",)
config.set(new_section, f"command{recover_command + 1}", "",)
config.set(new_section, f"command{new_recover_command}", "",)
# add files
config.set(new_section, "files", """utils/utils-school-idbroker.sh /root/
~/ec2/keys/tech.pem /root/.ssh/
""",)


config.write(sys.stdout)
