#!/bin/sh

# Install virtualbox guest-tools and delete script afterwards

# secure_apt=no because otherwise installation fails when app is installed from test appcenter
# E: The repository https://appcenter-test ... does not have a Release file.
ucr set --force update/secure_apt=no repository/online=yes
univention-install -y virtualbox-guest-utils
apt-get clean
ucr unset --force update/secure_apt repository/online

CONF='/etc/X11/xorg.conf.d/use-fbdev-driver.conf'
HOOK='/usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config'

mkdir -p "${CONF%/*}"
cat >"$CONF" <<__EOF__
Section "Device"
    Identifier  "Card0"
    Driver      "fbdev"
EndSection
__EOF__

cat >"$HOOK" <<__EOF__
#!/bin/sh
exec rm -f "$CONF"
__EOF__

chmod +x "$HOOK"

exec rm -- "$0"
