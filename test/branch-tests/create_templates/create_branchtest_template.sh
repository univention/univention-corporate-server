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
MEMORY=2097152

XML='<?xml version="1.0" ?>
<domain type="kvm">
  <name>${VERSION}_branchtest</name>
  <memory unit="KiB">${MEMORY}</memory>
  <currentMemory unit="KiB">${MEMORY}</currentMemory>
  <vcpu placement="static">1</vcpu>
  <resource>
    <partition>/machine</partition>
  </resource>
  <os>
    <type arch="x86_64" machine="pc-1.1">hvm</type>
    <boot dev="cdrom"/>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode="host-model">
    <model fallback="allow"/>
  </cpu>
  <clock offset="utc"/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/kvm</emulator>
    <disk device="disk" type="file">
      <driver cache="unsafe" name="qemu" type="qcow2"/>
      <source file="${VERSION}_branchtest-0.qcow2"/>
      <target bus="virtio" dev="vda"/>
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x04" type="pci"/>
    </disk>
    <controller index="0" type="ide">
      <address bus="0x00" domain="0x0000" function="0x1" slot="0x01" type="pci"/>
    </controller>
    <controller index="0" model="piix3-uhci" type="usb">
      <address bus="0x00" domain="0x0000" function="0x2" slot="0x01" type="pci"/>
    </controller>
    <controller index="0" model="pci-root" type="pci"/>
    <input bus="usb" type="tablet">
      <address bus="0" port="1" type="usb"/>
    </input>
    <input bus="ps2" type="mouse"/>
    <input bus="ps2" type="keyboard"/>
    <graphics autoport="yes" keymap="de" listen="0.0.0.0" port="-1" type="vnc">
      <listen address="0.0.0.0" type="address"/>
    </graphics>
    <video>
      <model heads="1" primary="yes" type="cirrus" vram="16384"/>
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x02" type="pci"/>
    </video>
    <memballoon model="virtio">
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x05" type="pci"/>
    </memballoon>
  </devices>
</domain>'

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

# extract the harddrive from the base appliance and copy
cd $TEMPLATE_BASE_BRANCH
tar --extract --wildcards --file=\$src '*_generic-unsafe-0.qcow2'
mv \${version}_generic-unsafe-0.qcow2 \${version}_branchtest-0.qcow2

# create xml  definition for template
export VERSION=\$version
export MEMORY=$MEMORY
echo '$XML' | envsubst > \${version}_branchtest.xml

# build template and clean up
tar -cvzf \${version}_branchtest_amd64.tar.gz \${version}_branchtest-0.qcow2 \${version}_branchtest.xml
rm -f \${version}_branchtest-0.qcow2
rm -f \${version}_branchtest.xml
"

exit 0
