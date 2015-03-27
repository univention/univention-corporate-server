/*
 * Copyright 2014-2015 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define require console setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/Deferred",
	"dojo/topic",
	"dijit/registry",
	"dijit/Menu",
	"dijit/PopupMenuItem",
	"dijit/MenuItem",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/app/ActivationPage!",  // page needs to be loaded as plugin
	"umc/app/ActivationDialog",
	"umc/i18n!umc/modules/udm"
], function(declare, kernel, lang, array, query, Deferred, topic, registry, Menu, PopupMenuItem, MenuItem, app, tools, dialog, ActivationPage, ActivationDialog, _) {

	var ucr = {};

	var _getLang = function() {
		return kernel.locale.split('-')[0];
	};

	var checkLicense = function() {
		tools.umcpCommand('udm/license', {}, false).then(function(data) {
			var msg = data.result.message;
			if (msg) {
				dialog.warn(msg);
			}
		}, function() {
			console.warn('WARNING: An error occurred while verifying the license. Ignoring error.');
		});
	};

	var _showLicenseImportDialog = function() {
		topic.publish('/umc/actions', 'menu-settings', 'license-import');
		require(['umc/modules/udm/LicenseImportDialog'], function(LicenseImportDialog) {
			var dlg = new LicenseImportDialog();
			dlg.show();
		});
	};

	var _showLicenseInformationDialog = function() {
		topic.publish('/umc/actions', 'menu-settings', 'license');
		require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
			var dlg = new LicenseDialog();
		});
	};

	var _showActivationDialog = function() {
		// The following check is only for if this dialogue is opened via topic.publish()
		if (ucr['uuid/license']) {
			dialog.alert(_('The license has already been activated.'));
			return;
		}

		new ActivationDialog({});
	};

	var addLicenseMenu = function() {
		var licenseMenu = new Menu({});
		if (!ActivationPage.hasLicense) {
			// license has not been activated yet
			licenseMenu.addChild(new MenuItem({
				label: _('Activation of UCS'),
				onClick: _showActivationDialog
			}), 0);
		}

		licenseMenu.addChild(new MenuItem({
			label: _('Import new license'),
			onClick : _showLicenseImportDialog
		}), 0);
		licenseMenu.addChild(new MenuItem({
			label: _('License information'),
			onClick : _showLicenseInformationDialog
		}), 0);

		app.addMenuEntry(new PopupMenuItem({
			$priority$: 80,
			label: _('License'),
			id: 'umcMenuLicense',
			popup: licenseMenu
		}));
	};

	topic.subscribe('/umc/license/activation', _showActivationDialog);

	return function() {
		checkLicense();
		tools.ucr(['uuid/license']).then(function(_ucr) {
			lang.mixin(ucr, _ucr);
			addLicenseMenu();
		});
	};
});
