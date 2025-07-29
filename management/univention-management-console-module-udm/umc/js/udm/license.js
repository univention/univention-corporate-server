/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,require*/

define([
	"dojo/topic",
	"umc/menu",
	"umc/i18n!umc/modules/udm"
], function(topic, menu, _) {
	var _showLicenseImportDialog = function() {
		topic.publish('/umc/actions', 'menu', 'license', 'import');
		require(['umc/modules/udm/LicenseImportDialog'], function(LicenseImportDialog) {
			var dlg = new LicenseImportDialog();
			dlg.show();
		});
	};

	var _showLicenseInformationDialog = function() {
		topic.publish('/umc/actions', 'menu', 'license', 'info');
		require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
			new LicenseDialog();
		});
	};

	menu.addSubMenu({
		priority: 80,
		label: _('License'),
		id: 'umcMenuLicense',
	});

	menu.addEntry({
		priority: 20,
		label: _('Import new license'),
		onClick : _showLicenseImportDialog,
		parentMenuId: 'umcMenuLicense'
	});
	menu.addEntry({
		priority: 10,
		label: _('License information'),
		onClick : _showLicenseInformationDialog,
		parentMenuId: 'umcMenuLicense'
	});

	return null;
});
