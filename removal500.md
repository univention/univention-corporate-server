# Clean uninstall

## [nagios/univention-nagios-ad-connector/](nagios/univention-nagios-ad-connector/)
- [x] UCR `/etc/nagios-plugins/config/`
- [x] JOIN `31univention-nagios-ad-connector.inst`	OKAY
- [x] JOIN `69univention-nagios-ad-connector.uinst`

## [nagios/univention-nagios-s4-connector/](nagios/univention-nagios-s4-connector/)
- [x] UCR /`etc/nagios-plugins/config/`
- [x] JOIN `31univention-nagios-s4-connector.inst` OKAY
- [x] JOIN `69univention-nagios-s4-connector.uinst`

## [base/univention-runit/](base/univention-runit/)
- [x] -

## [base/univention-doc/](base/univention-doc/)
- [x] UCR `/etc/apache2/sites-available`
- [x] UCRV `ucs/web/overview/entries/admin/univention-doc/`

## [kernel/univention-kernel-image-signed/](kernel/univention-kernel-image-signed/)
- [x] -

## [base/univention-debootstrap/](base/univention-debootstrap/)
- [x] -

# Requires purge

## [desktop/univention-kdm/](desktop/univention-kdm/)
- [x] UCR `/etc/default/kdm.d`
- [ ] UCRV `kdm/usetheme`
- [ ] UCRV `kdm/theme`

## [desktop/univention-mozilla-firefox/](desktop/univention-mozilla-firefox/)
- [x] UCR `/etc/firefox-esr`
- [ ] UCRV `firefox/prefs/homepage`
- [ ] UCRV `firefox/prefs/spellchecker/dictionary`
- [ ] UCRV `firefox/prefs/conffile`
- [ ] UCRV `firefox/prefs/checkdefaultbrowser`
- [ ] UCRV `kerberos/defaults/rdns`
- [ ] DIR `/etc/univention/skel/Downloads`
- [ ] ALT `/usr/bin/x-www-browser`

## [desktop/univention-x-core/](desktop/univention-x-core/)
- [x] UCR `/etc/X11`
- [x] UCR `/etc/securetty`
- [ ] UCRV `univentionXModule`
- [ ] UCRV `univentionXResolution`
- [ ] UCRV `univentionXColorDepth`
- [ ] UCRV `univentionXHSync`
- [ ] UCRV `univentionVertRefresh`
- [ ] UCRV `univentionXMouseDevice`
- [ ] UCRV `X/Mouse/Device`
- [ ] UCRV `univentionXDisplaySize`
- [ ] UCRV `X/Monitor/DisplaySize`
- [ ] UCRV `univentionXVideoRam`
- [ ] UCRV `univentionXKeyboardVariant`
- [ ] UCRV `univentionXKeyboardLayout`
- [ ] UCRV `xorg/**`

## [services/univention-ftp/](services/univention-ftp/)
- [x] UCRV `security/packetfilter/package/univention-ftp/**`

## [services/univention-check-printers/](services/univention-check-printers/)
- [x] UCR `/etc/cron.d/univention-check-printers`
- [ ] UCRV `cups/checkprinters/`

## [base/univention-skel/](base/univention-skel/)
- [x] UCRV `skel/**`

## [services/univention-snmp/](services/univention-snmp/)
- [x] UCRV `security/packetfilter/package/univention-snmp/**`

## [services/univention-snmpd/](services/univention-snmpd/)
- [x] UCRV `security/packetfilter/package/univention-snmpd/**`

## [nagios/univention-nagios-samba/](nagios/univention-nagios-samba/)
- [x] UCR `/etc/nagios-plugins/config/`
- [x] JOIN `31univention-nagios-samba.inst`	OKAY
- [x] JOIN `69univention-nagios-samba.uinst`

# Should have un-join script to remove registration

## [services/univention-samba4wins/](services/univention-samba4wins/)
- [x] JOIN `90univention-samba4wins.inst`	OKAY
- [x] JOIN `10univention-samba4wins.uinst`
- [x] JOIN `89univention-samba4wins-schema.inst`	OKAY
- [x] JOIN `11univention-samba4wins-schema.uinst`
- [x] UCR `/etc/samba/smb.conf.d/`
- [x] UCR `/etc/ldap/slapd.conf.d`
- [x] UCR `/etc/samba4wins/`
- [ ] LISTENER
- [ ] SCHEMA `univention-samba4wins.schema`

## [nagios/univention-nagios-raid/](nagios/univention-nagios-raid/)
- [ ] JOIN `31univention-nagios-raid.inst`

## [nagios/univention-nagios-servicechecks/](nagios/univention-nagios-servicechecks/)
- [x] UCR `/etc/nagios-plugins/config/`
- [ ] JOIN `35univention-nagios-cups.inst`
- [ ] JOIN `35univention-nagios-opsi.inst`
- [ ] JOIN `35univention-nagios-squid.inst`
- [x] JOIN `35univention-nagios-dansguardian.inst` OKAY
- [x] JOIN `65univention-nagios-dansguardian.uinst` OKAY

## [nagios/univention-nagios-smart/](nagios/univention-nagios-smart/)
- [x] UCR `/etc/nagios-plugins/config/`
- [ ] JOIN `31univention-nagios-smart.inst`

## [nagios/univention-nagios/](nagios/univention-nagios/)
- [x] UCR `/etc/`
- [ ] UCRV `nagios/client/checkraid`
- [ ] UCRV `nagios/client/autostart`
- [ ] UCRV `security/packetfilter/package/univention-nagios-client/**`
- [ ] DIR `/var/lib/univention-nagios/check_univention_replication.cache`
- [x] JOIN `26univention-nagios-common.inst`
- [x] JOIN `28univention-nagios-server.inst`	OKAY
- [ ] JOIN `28univention-nagios-server.uinst`
- [ ] JOIN `30univention-nagios-client.inst`
- [ ] UCRV `nagios/common/defaultservices/autocreate`
- [ ] UCRV `nagios/server/**`
- [x] UCRV `ucs/web/overview/entries/admin/nagios/**`	OKAY
- [ ] UCRV `auth/nagios/**`
- [ ] DIR `/var/cache/nagios/`
- [ ] DIR `/var/log/nagios/`
- [ ] DIR `/etc/nagios/conf.univention.d/`
- [x] APACHE enconf nagios	OKAY

## UVMM
* <https://forge.univention.org/bugzilla/show_bug.cgi?id=51982>
### [nagios/univention-nagios-virtualization/](nagios/univention-nagios-virtualization/)
### [virtualization/univention-kvm-compat/](virtualization/univention-kvm-compat/)
### [virtualization/univention-kvm-virtio/](virtualization/univention-kvm-virtio/)
### [virtualization/univention-novnc/](virtualization/univention-novnc/)
### [virtualization/univention-virtual-machine-manager-daemon/](virtualization/univention-virtual-machine-manager-daemon/)
### [virtualization/univention-virtual-machine-manager-node/](virtualization/univention-virtual-machine-manager-node/)
### [virtualization/univention-virtual-machine-manager-schema/](virtualization/univention-virtual-machine-manager-schema/)

## [desktop/univention-kde/](desktop/univention-kde/)
- [ ] JOIN `78univention-kde.inst`
- [x] UCR `/etc/dbus-1/system.d`
- [x] UCR `/usr/share`
- [ ] UCRV `auth/kdeprofile`
- [ ] UCRV `hal/devices/group`
- [ ] DPKG-STAT `/usr/lib/kde4/libexec/kcheckpass`
- [ ] FILES `/usr/share/univention-kde-profiles`

## [services/univention-dansguardian/](services/univention-dansguardian/)
* <https://forge.univention.org/bugzilla/show_bug.cgi?id=52962>
- [ ] JOIN `79univention-dansguardian.inst`
- [x] UCR `dansguardian-filtergroups.py`
- [x] UCR `/etc/dansguardian/`
- [x] UCRV `squid/virusscan`
- [x] UCRV `squid/contentscan`
- [ ] UCRV `dansguardian/**`
- [ ] UCRV `clamav/freshclam/autostart`	?
- [x] UCRV `security/packetfilter/package/univention-dansguardian/**`

## [management/univention-management-console-module-mrtg/](management/univention-management-console-module-mrtg/)
- [ ] INST `35univention-management-console-module-mrtg.inst`

# Must cleanup DB, user, uinst, DIRS, secrets, ...

## [services/univention-printquota/](services/univention-printquota/)
* <https://forge.univention.org/bugzilla/show_bug.cgi?id=51482>
- [x] JOIN `80univention-printquota.inst`	OKAY
- [x] JOIN `20univention-printquota.uinst`
- [x] UCR `/etc/pykota/**`
- [x] UCR `/etc/postgresql/9.?/main/pg_hba.conf.d/`
- [ ] ADDUSER `pykota`
- [ ] UCRV `pykota/policy/debug`
- [ ] DPKG-STAT `/usr/share/pykota/cupspykota`
- [ ] POSTGRESQL
- [ ] DIR `/etc/pykota`
- [x] FILE `/etc/pykota/pykota.secret`
- [ ] UCRV `cups/quota/secret`
- [ ] UCRV `cups/quota/server/access`

## [services/univention-bacula/](services/univention-bacula/)
- [x] UCR `/etc/postgresql/9.?/main/pg_hba.conf.d/`
- [ ] POSTGRESQL
- [ ] UCRV `bacula/`
- [ ] UCRV `security/packetfilter/package/univention-bacula/**`

## [base/univention-passwd-cache/](base/univention-passwd-cache/)
- [ ] RM `/etc/univention/passwdcache/shadow`

# Breaks afer uninstall

## [base/univention-passwd-store/](base/univention-passwd-store/)
- [ ] UCR.rm `/etc/pam.d/common-auth.d/`
- [ ] UCR.rm `/etc/pam.d/common-session.d/`
- [ ] UCRV.unset `auth/passwdstore`

## [services/univention-remote-backup/](services/univention-remote-backup/)
- [ ] DIR.rm `/home/backup`
- [ ] CRON.test
