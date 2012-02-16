PATH=/usr/sbin:/usr/bin:/sbin:/bin

@reboot root /usr/sbin/univention-upgrade --noninteractive ; univention-config-registry set update/reboot/required=false
