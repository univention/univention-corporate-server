#!/bin/bash
export KVM_KEYPAIR_PASSPHRASE=univention
export UCS_ENV_PASSWORD=univention
exec ./utils/start-test.sh ./scenarios/autotest-247-ucsschool-id-broker-perf.cfg
