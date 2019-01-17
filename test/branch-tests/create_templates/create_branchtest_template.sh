#!/bin/bash

set -x
set -e

env

USER=build
SERVER=omar
VERSION=$TEMPLATE_VERSION

TEMPLATE_BASE_BRANCH="/mnt/omar/vmwares/kvm/single/Others"
TEMPLATE_BASE_UCS="/mnt/omar/vmwares/kvm/single/UCS"
TEMPLATE_XML="${TEMPLATE_BASE_BRANCH}/branchtest_template.xml"

mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$USER" "$SERVER" "$@"
}


mssh "

set -x
set -e

# check if there is already a branch test ucs-kt-get template
if ls '${TEMPLATE_BASE_BRANCH}/${VERSION}'+*_branchtest_amd64.tar.gz; then
	echo 'branchtest template already exists, bye'
	exit 0
fi

# check if there is a normal ucs-kt-get template for this version
if ! ls '${TEMPLATE_BASE_UCS}/${VERSION}'+*_generic-unsafe_amd64.tar.gz; then
	echo 'branchtest could not be created, the UCS kt-get template is missing'
	exit 1
fi


src=\$(ls -t ${TEMPLATE_BASE_UCS}/${VERSION}+*_generic-unsafe_amd64.tar.gz | head -1)
src_file=\$(basename \$src)
version=\${src_file%%_*}

# extract the harddrive and create new template
cd $TEMPLATE_BASE_BRANCH
tar --get -f \$src \${version}_generic-unsafe-0.qcow2
mv \${version}_generic-unsafe-0.qcow2 \${version}_branchtest-0.qcow2
VERSION=\$version envsubst < $TEMPLATE_XML > \${version}_branchtest.xml
tar -cvzf \${version}_branchtest_amd64.tar.gz \${version}_branchtest-0.qcow2 \${version}_branchtest.xml
rm -f \${version}_branchtest-0.qcow2
rm -f \${version}_branchtest.xml
"

exit 0
