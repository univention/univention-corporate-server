#!/bin/bash

# Install virtualbox guest-tools and delete script afterwards

# secure_apt=no because otherwise installation fails when app is installed from test appcenter
# E: The repository https://appcenter-test ... does not have a Release file.
ucr set --force update/secure_apt=no repository/online=yes
univention-install -y virtualbox-guest-utils
apt-get clean
ucr unset --force update/secure_apt repository/online

mkdir -p /etc/X11/xorg.conf.d
cat >/etc/X11/xorg.conf.d/use-fbdev-driver.conf <<__EOF__
Section "Device"
    Identifier  "Card0"
    Driver      "fbdev"
EndSection
__EOF__

cat >/usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config <<__EOF__
#!/bin/sh
rm /etc/X11/xorg.conf.d/use-fbdev-driver.conf
exit 0
__EOF__

chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config

rm -- "$0"
