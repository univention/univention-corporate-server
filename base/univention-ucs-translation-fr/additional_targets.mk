$(SPECIAL_TARGETS) = $(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-system-setup-scripts.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-root-login-notification.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-appcenter.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-appcenter.mo \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-directory-reports.mo \
	$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json \
	$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo

$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-system-setup-scripts.mo: fr/base/univention-system-setup/usr/share/locale/fr/LC_MESSAGES/univention-system-setup-scripts.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-root-login-notification.mo: fr/desktop/univention-kde/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-admin-handlers-appcenter.mo: fr/management/univention-appcenter/udm/handlers/appcenter/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-appcenter.mo: management/univention-appcenter/python/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-directory-reports.mo: fr/management/univention-directory-reports/modules/univention/directory/reports/fr.po
$(DESTDIR)/usr/share/univention-self-service/www/js/ucs/fr.json: fr/management/univention-directory-reports/modules/univention/directory/reports/fr.po
$(DESTDIR)/usr/share/locale/fr/LC_MESSAGES/univention-management-console-handlers-cups.mo: services/univention-printserver/modules/univention/management/console/handlers/cups/fr.po
