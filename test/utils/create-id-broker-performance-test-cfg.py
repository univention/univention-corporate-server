#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
from configparser import ConfigParser

template_file = "scenarios/autotest-247-ucsschool-id-broker.cfg"


config = ConfigParser(interpolation=None)
config.read(template_file)
sections = config.sections()
sections.remove("Global")
recover_command = int(config.get("Global", "recover"))
new_recover_command = recover_command + 1

config.set("Global", "recover", str(new_recover_command))

label = config.get("Global", "kvm_extra_label")
config.set("Global", "kvm_extra_label", f"{label}-performance")

for section in sections:
    command = config.get(section, f"command{recover_command}")
    config.set(section, f"command{recover_command}", "")
    config.set(section, f"command{new_recover_command}", command)

new_section = "JumpHost"
config.add_section(new_section)
config.set(new_section, "kvm_template", "[ENV:KVM_TEMPLATE]")
config.set(new_section, "kvm_ucsversion", "[ENV:KVM_UCSVERSION]")
for i in range(1, recover_command - 1):
    config.set(new_section, f"command{i}", "")
if not os.environ.get("UCS_ENV_ID_BROKER_STAGING") in ["kvm", "staging", "local"]:
    raise Exception("you need to set UCS_ENV_ID_BROKER_STAGING to either kvm, staging or local")

# add test section kvm -> ./utils/start-id-broker-performance-tests-kvm.sh
if os.environ["UCS_ENV_ID_BROKER_STAGING"] == "kvm":
    config.set(new_section, f"command{recover_command}", """
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
. utils-school-idbroker.sh && add_to_ssh_environment "TRAEGER1_FQDN=traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "TRAEGER2_FQDN=traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "SELF_DISCLOSURE_FQDN=self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "PROVISIONING_FQDN=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "KEYCLOAK_FQDN=login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "BROKER_LDAPS=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN] self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN] idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN] kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
#
. utils-school-idbroker.sh && prepare_jump_host
/usr/share/id-broker-performance-tests/run_tests""")
# add test section for local -> ./utils/start-id-broker-performance-tests-local.sh
elif os.environ["UCS_ENV_ID_BROKER_STAGING"] == "local":
    config.set(new_section, f"command{recover_command}", """
. utils.sh && basic_setup
. utils.sh && rotate_logfiles
. utils.sh && activate_idbroker_devel_scope
#
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_TRAEGER1_IP]" "traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_TRAEGER2_IP]" "traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN] ucs-sso.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_PRIMARY_IP]" "idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_PROVISIONING_IP]" "provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_SELFDISCLOSURE_IP]" "self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_hosts "[ENV:UCS_ENV_KEYCLOAK_IP]" "kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN] login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "TRAEGER1_FQDN=traeger1.[ENV:UCS_ENV_TRAEGER1_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "TRAEGER2_FQDN=traeger2.[ENV:UCS_ENV_TRAEGER2_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "SELF_DISCLOSURE_FQDN=self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "PROVISIONING_FQDN=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "KEYCLOAK_FQDN=login.kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
. utils-school-idbroker.sh && add_to_ssh_environment "BROKER_LDAPS=provisioning1.[ENV:UCS_ENV_IDBROKER_DOMAIN] self-disclosure1.[ENV:UCS_ENV_IDBROKER_DOMAIN] idbroker-primary.[ENV:UCS_ENV_IDBROKER_DOMAIN] kc1.[ENV:UCS_ENV_IDBROKER_DOMAIN]"
#
. utils-school-idbroker.sh && prepare_jump_host
/usr/share/id-broker-performance-tests/run_tests""")
# add test section for staging ./utils/start-id-broker-performance-tests-staging.sh
elif os.environ["UCS_ENV_ID_BROKER_STAGING"] == "staging":
    raise NotImplementedError()
else:
    raise NotImplementedError()

# add fetch-results section
config.set(new_section, f"command{new_recover_command}", f"""
.  utils.sh && prepare_results
LOCAL utils/utils-local.sh fetch-results [{new_section}_IP] {new_section}
LOCAL utils/utils-local.sh fetch-files "root@[{new_section}_IP]" '*.csv' locust
LOCAL utils/utils-local.sh fetch-files "root@[{new_section}_IP]" '*.html' locust
""")

# add files
config.set(new_section, "files", """utils/utils-school-idbroker.sh /root/
~/ec2/keys/tech.pem /root/.ssh/
""")

# remove everything except the jump host for staging or local tests
if os.environ["UCS_ENV_ID_BROKER_STAGING"] in ["staging", "local"]:
    sections_to_remove = config.sections()
    sections_to_remove.remove("Global")
    sections_to_remove.remove("JumpHost")
    for section in sections_to_remove:
        config.remove_section(section)

config.write(sys.stdout)
