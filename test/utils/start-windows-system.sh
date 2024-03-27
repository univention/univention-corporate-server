#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export TERMINATE=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false

# user specific instances "username_..."
export KVM_OWNER="${BUILD_USER_ID:=$USER}"
export JOB_BASE_NAME="${JOB_BASE_NAME:=windows-os}"

WINDOWS_OS="${WINDOWS_OS:=win10}"

case "$WINDOWS_OS" in
    win10)
        export WINDOWS_kvm_ucsversion="win10"
        export WINDOWS_kvm_template="de-winrm-credssp"
        ;;
    win11)
        export WINDOWS_kvm_ucsversion="win11"
        export WINDOWS_kvm_template="en-winrm-credssp"
        ;;
    win2019)
        export WINDOWS_kvm_ucsversion="2019-server"
        export WINDOWS_kvm_template="de-winrm-credssp"
        ;;
    win2012)
        export WINDOWS_kvm_ucsversion="2012"
        export WINDOWS_kvm_template="de-winrm-credssp"
        ;;
    *)
        echo "Unknown windows version, no template"
        exit 1
        ;;
esac

exec ./utils/start-test.sh scenarios/base/windows-system.cfg
