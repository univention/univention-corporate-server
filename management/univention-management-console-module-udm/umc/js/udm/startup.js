/*
 * Copyright 2014-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/Deferred",
	"dojo/topic",
	"dijit/registry",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"management/widgets/ActivationPage!",  // page needs to be loaded as plugin
	"management/widgets/ActivationDialog",
	"umc/i18n!umc/modules/udm"
], function(declare, kernel, lang, array, query, Deferred, topic, registry, menu, tools, dialog, ActivationPage, ActivationDialog, _) {

	var ucr = {};

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

	var _showActivationDialog = function() {
		// The following check is only for if this dialogue is opened via topic.publish()
		if (ucr['uuid/license']) {
			dialog.alert(_('The license has already been activated.'));
			return;
		}

		topic.publish('/umc/actions', 'menu', 'license', 'activation');
		new ActivationDialog({});
	};

	var addActivationMenu = function() {
		if (!ActivationPage.hasLicense) {
			// license has not been activated yet
			menu.addEntry({
				priority: 30,
				label: _('Activation of UCS'),
				onClick: _showActivationDialog,
				parentMenuId: 'umcMenuLicense'
			});
		}
	};

	topic.subscribe('/umc/license/activation', _showActivationDialog);

	return function() {
		checkLicense();
		tools.ucr(['uuid/license']).then(function(_ucr) {
			lang.mixin(ucr, _ucr);
			addActivationMenu();
		});
	};
});
