# ucs-kt-get templates

This directory holds files for creating ucs-kt-get (KVM) templates. With these
templates you can easily set up UCS domains without
provisioning/configuration.

## Current templates

- generic-unsafe
- ucs-master|ucs-backup|ucs-slave|ucs-member
- ucs-joined-master|ucs-joined-backup|ucs-joined-slave|ucs-joined-member
- ucs-school-singleserver-joined TODO
- ucs-samba-primary|ucs-samba-replica

## Usage

### Interactive

- ssh KVM_SERVER
- ucs-kt-get 

or

- ucs-kt-get -O Others ucs-joined-backup

## Add new templates

### New scenario file

### New Jenkins job for creating the templates
