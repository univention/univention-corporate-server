ADDITIONAL = $(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-system-setup-scripts.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-root-login-notification.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-appcenter.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-appcenter.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-directory-reports.mo \
	$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo \
	$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json \
	$(DESTDIR)/var/www/ucs-overview/js/ucs/fr.json \
	$(DESTDIR)/var/www/ucs-overview/js/ci-appliance/fr.json \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-settings-mswmifilter.mo \
	$(DESTDIR)/usr/share/locale/de/LC_MESSAGES/univention-admin-handlers-settings-msprintconnectionpolicy.mo


$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-system-setup-scripts.mo: fr/base/univention-system-setup/usr/share/locale/de/LC_MESSAGES/univention-system-setup-scripts.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-root-login-notification.mo: fr/desktop/univention-kde/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-appcenter.mo: fr/management/univention-appcenter/udm/handlers/appcenter/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-appcenter.mo: fr/management/univention-appcenter/python/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-directory-reports.mo: fr/management/univention-directory-reports/modules/univention/directory/reports/fr.po
$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json: fr/management/univention-directory-reports/modules/univention/directory/reports/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo: fr/services/univention-printserver/modules/univention/management/console/handlers/cups/fr.po
$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json:  fr/management/univention-self-service/js/ucs/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-saml.mo: fr/saml/univention-saml/fr.po
$(DESTDIR)/var/www/ucs-overview/js/ucs/fr.json: fr/services/univention-apache/js/ucs/fr.po
$(DESTDIR)/var/www/ucs-overview/js/ci-appliance/fr.json: fr/services/univention-cloud-init/var/www/ucs-overview/js/ci-appliance/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo: fr/services/univention-printserver/modules/univention/management/console/handlers/cups/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-settings-mswmifilter.mo: fr/services/univention-s4-connector/modules/univention/admin/handlers/settings/mswmifilter/fr.po
$(DESTDIR)/usr/share/locale/de/LC_MESSAGES/univention-admin-handlers-settings-msprintconnectionpolicy.mo: fr/services/univention-s4-connector/modules/univention/admin/handlers/settings/msprintconnectionpolicy/fr.po
