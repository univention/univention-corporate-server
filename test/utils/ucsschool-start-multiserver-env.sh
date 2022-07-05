#!/bin/bash
set -x
set -e
export HALT=false
export DOCKER=true
export KVM_LABEL_SUFFIX="${Config}-${UCSRelease}"
export release_update="$UCSRelease"
export errata_update="$UCSRelease"
export RELEASE_UPDATE="$UCSRelease"
export ERRATA_UPDATE="$UCSRelease"
export UCS_TEST_RUN=false

# TODO remove
export DIMAGE="docker-registry.knut.univention.de/ucs-ec2-tools:branch-fbotner-issue-13"

# user specific instances "username_..."
if [ -n "$BUILD_USER_ID" ]; then
	export UCS_ENV_UCS_KT_GET_USERNAME="$BUILD_USER_ID"
fi

cfg="scenarios/autotest-203-ucsschool-multiserver-s4.cfg"
if [ "${Config}" = "s4-all-components" ] ; then
  sed -i -re '/^ packages_install/s/"$/ univention-mail-server univention-dhcp univention-printserver cups univention-squid bsd-mailx univention-spamassassin univention-antivir-mail"/' "$cfg"
fi
exec utils/start-test.sh "$cfg"
