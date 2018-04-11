#!/bin/bash

# Install virtualbox guest-tools and delete script afterwards

ucr set repository/online/unmaintained=yes repository/online=yes
univention-install -y virtualbox-guest-utils
apt-get clean
ucr set repository/online/unmaintained=no repository/online=no
apt-get update

rm -- "$0"
