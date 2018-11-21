#!/bin/bash

# Install virtualbox guest-tools and delete script afterwards

# secure_apt=no because otherwise installation fails when app is installed from test appcenter
# E: The repository https://appcenter-test ... does not have a Release file.
ucr set update/secure_apt=no
ucr set repository/online/unmaintained=yes repository/online=yes
univention-install -y virtualbox-guest-utils
apt-get clean
ucr set update/secure_apt=yes
ucr set repository/online/unmaintained=no repository/online=no
apt-get update

rm -- "$0"
