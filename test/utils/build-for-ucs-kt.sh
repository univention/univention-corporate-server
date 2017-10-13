#!/bin/bash

set -x
set -e

APP_ID="$1"

IMG="/tmp/Univention-App-${APP_ID}-KVM.qcow2"
META="/tmp/appliance_${APP_ID}_amd.xml"
ARCHIVE="/tmp/appliance_${APP_ID}_amd64.tar"
MASTER_IMAGE="/tmp/master-image"

function finish {
	rm -v "$META" || true
	rm -v "$IMG" || true
	rm -v "$MASTER_IMAGE" || true
	rm -v "$ARCHIVE" || true  # should fail if everything went right
	rm -v "$ARCHIVE".gz || true  # should fail if everything went right
}

trap finish EXIT

APP="$APP_ID" envsubst </mnt/omar/vmwares/kvm/single/Others/appliance_template.xml >"$META"
tar -C "$(dirname "$META")" -cf "$ARCHIVE" "$(basename "$META")"
tar -C "$(dirname "$IMG")" -rf "$ARCHIVE" "$(basename "$IMG")"
touch "$MASTER_IMAGE"  # what is this for?
tar -C "$(dirname "$MASTER_IMAGE")" -rf "$ARCHIVE" "$(basename "$MASTER_IMAGE")"
gzip -9 "$ARCHIVE"
mv "$ARCHIVE".gz /mnt/omar/vmwares/kvm/single/Others/appliance_"${APP_ID}"_amd64.tar.gz
