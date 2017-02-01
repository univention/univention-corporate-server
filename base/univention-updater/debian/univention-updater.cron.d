PATH=/usr/sbin:/usr/bin:/sbin:/bin

@reboot root /usr/share/univention-updater/enable-apache2-umc
@reboot root /usr/share/univention-updater/updater-statistics > /dev/zero
@daily  root /usr/share/univention-updater/updater-statistics > /dev/zero
