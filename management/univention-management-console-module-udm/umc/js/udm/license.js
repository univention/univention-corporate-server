/*
 * Copyright 2017-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
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
