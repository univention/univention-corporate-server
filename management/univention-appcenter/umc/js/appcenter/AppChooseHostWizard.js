/*
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/_base/array",
	"dojox/html/entities",
	"umc/widgets/Wizard",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, entities, Wizard, Text, ComboBox, _) {
	return declare('umc.modules.appcenter.AppChooseHostWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',

		app: null,

		needsToBeShown: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = this._getPages();
		},

		_getPages: function() {
			var hosts = [];
			var removedDueToInstalled = [];
			var removedDueToRole = [];
			if (this.app.installationData) {
				array.forEach(this.app.installationData, function(item) {
					if (item.canInstall()) {
						if (item.isLocal()) {
							hosts.unshift({
								label: item.displayName,
								id: item.fqdn
							});
						} else {
							hosts.push({
								label: item.displayName,
								id: item.fqdn
							});
						}
					} else {
						if (item.isInstalled) {
							removedDueToInstalled.push(item.displayName);
						} else if (!item.hasFittingRole()) {
							removedDueToRole.push(item.displayName);
						}
					}
				});
			}

			var removeExplanation = '';
			if (removedDueToInstalled.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application is installed on this host.', entities.encode(removedDueToInstalled[0])) + '</p>';
			} else if (removedDueToInstalled.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application is installed there.', removedDueToInstalled.length) + '</p>';
			}
			if (removedDueToRole.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application requires a different server role than the one this host has.', entities.encode(removedDueToRole[0])) + '</p>';
			} else if (removedDueToRole.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application requires a different server role than these hosts have.', removedDueToRole.length) + '</p>';
			}
			if (removeExplanation) {
				removeExplanation = '<strong>' + _('Not all hosts are listed above') + '</strong>' + removeExplanation;
			}

			this.needsToBeShown = hosts.length > 1 || !!removedDueToInstalled.length || !!removedDueToRole.length;
			return  [{
				name: 'chooseHost',
				headerText: _('Installation of %s', this.app.name),
				widgets: [{
					type: Text,
					name: 'infoText',
					content: _('In order to proceed with the installation of %s, please select the host on which the application is going to be installed.', this.app.name)
				}, {
					type: ComboBox,
					label: _('Host for installation of application'),
					name: 'host',
					required: true,
					size: 'Two',
					staticValues: hosts
				}, {
					type: Text,
					name: 'removeExplanation',
					content: removeExplanation
				}]
			}];
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, function(button) {
				if (button.name === 'finish') {
					button.label = _('Continue');
				}
			});
			return buttons;
		}
	});
});



