/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
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
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/widgets/ComboBox",
	"umc/widgets/Text",
	"umc/widgets/Wizard",
	"./AppText",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, domClass, entities, _WidgetBase, _TemplatedMixin, ComboBox, Text, Wizard, AppText, _) {
	return declare('umc.modules.appcenter.AppChooseHostWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',

		// TODO this does not work
		autoHeight: true,


		// these need to be provided
		apps: null,
		auto_installed: null,
		// these need to be provided
		//
		selectedApps: null,


		needsToBeShown: null,
		_chooseHostsNeedsToBeShown: null,
		autoValidate: true,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.selectedApps = this.apps.filter(app => !this.auto_installed.includes(app.id));
			this.pages = this._getPages();
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppChooseHostWizard');
		},

		_getAppsPage: function(headerText) {
			const page = {
				name: 'appsOverview',
				headerText: headerText,
				widgets: [],
				layout: [],
			};
			if (this.auto_installed.length) {
				let infoText = '';
				if (this.selectedApps.length === 1) {
					if (this.auto_installed.length === 1) {
						infoText = _('The following App will be additionally installed because it is a required dependency for %s.', this.selectedApps[0].name);
					} else {
						infoText = _('The following Apps will be additionally installed because they are required dependencies for %s.', this.selectedApps[0].name);
					}
				} else {
					if (this.auto_installed.length === 1) {
						infoText = _('The following App will be additionally installed because it is a required dependency for the selected Apps.');
					} else {
						infoText = _('The following Apps will be additionally installed because they are required dependencies for the selected Apps.');
					}
				}
				page.widgets.push({
					type: Text,
					name: 'appsOverview_text',
					content: infoText
				});
				page.layout.push('appsOverview_text');
				page.layout.push([]);
				for (const appId of this.auto_installed) {
					const app = this.apps.find(app => app.id === appId);
					const name = `appOverview_appText_${app.id}`;
					page.widgets.push({
						type: AppText,
						app: AppText.appFromApp(app),
						name,
						size: 'One',
					});
					const layout = page.layout[page.layout.length - 1];
					if (layout.length < 2) {
						layout.push(name);
					} else {
						page.layout.push([name]);
					}
				}
			}

			if (this.selectedApps.length > 1) {
				let infoText = '';
				if (!this.auto_installed.length) {
					infoText = _('The following Apps are going to be installed.');
				} else {
					infoText = _('The following Apps where initially selected.');
				}
				page.widgets.push({
					type: Text,
					name: 'appsOverview_text2',
					content: infoText,
				});
				page.layout.push('appsOverview_text2');
				page.layout.push([]);
				for (const app of this.selectedApps) {
					const name = `appOverview_appText_${app.id}`;
					page.widgets.push({
						type: AppText,
						app: AppText.appFromApp(app),
						name,
						size: 'One',
					});
					const layout = page.layout[page.layout.length - 1];
					if (layout.length < 2) {
						layout.push(name);
					} else {
						page.layout.push([name]);
					}
				}
			}
			return page;
		},

		_getChooseHostPage: function(headerText) {
			const infoText = this.selectedApps.length === 1
				? _('In order to proceed with the installation of %s, please select the host on which the App is going to be installed.', this.selectedApps[0].name)
				: _('In order to proceed with the installation, please select the hosts on which the Apps are going to be installed.');
			const page = {
				name: 'chooseHosts',
				headerText: headerText,
				widgets: [{
					type: Text,
					name: 'chooseHosts_infoText',
					content: infoText
				}],
				layout: [
					'chooseHosts_infoText'
				]
			};
			for (const app of this.apps) {
				var hosts = [];
				var removedDueToInstalled = [];
				var removedDueToRole = [];
				if (app.installationData) {
					array.forEach(app.installationData, function(item) {
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
					removeExplanation += '<p>' + _('%s was removed from the list because the App is installed on this host.', entities.encode(removedDueToInstalled[0])) + '</p>';
				} else if (removedDueToInstalled.length > 1) {
					removeExplanation += '<p>' + _('%d hosts were removed from the list because the App is installed there.', removedDueToInstalled.length) + '</p>';
				}
				if (removedDueToRole.length === 1) {
					removeExplanation += '<p>' + _('%s was removed from the list because the App requires a different server role than the one this host has.', entities.encode(removedDueToRole[0])) + '</p>';
				} else if (removedDueToRole.length > 1) {
					removeExplanation += '<p>' + _('%d hosts were removed from the list because the App requires a different server role than these hosts have.', removedDueToRole.length) + '</p>';
				}
				if (removeExplanation) {
					removeExplanation = '<strong>' + _('Not all hosts are listed above') + '</strong>' + removeExplanation;
				}

				page.widgets.push({
					type: AppText,
					app: AppText.appFromApp(app),
					size: 'One',
					name: `chooseHosts_appText_${app.id}`,
				});
				page.widgets.push({
					type: ComboBox,
					label: _('Host for installation of App'),
					name: app.id,
					required: true,
					size: 'One',
					staticValues: hosts
				});
				page.layout.push([`chooseHosts_appText_${app.id}`, app.id]);
				if (removeExplanation) {
					page.widgets.push({
						type: Text,
						name: `chooseHosts_removeExplanation_${app.id}`,
						content: removeExplanation,
						'class': 'umcAppChooseHostWizard__removeExplanation'
					});
					page.layout.push(`chooseHosts_removeExplanation_${app.id}`);
				}

				this._chooseHostsNeedsToBeShown = this._chooseHostsNeedsToBeShown
					|| (hosts.length > 1 || !!removedDueToInstalled.length || !!removedDueToRole.length);
			}
			return page;
		},

		_getPages: function() {
			const pages = [];
			const headerText = this.selectedApps.length === 1
				? _('Installation of %s', this.selectedApps[0].name)
				: _('Installation of multiple apps');
			pages.push(this._getAppsPage(headerText));
			pages.push(this._getChooseHostPage(headerText));
			this._showToBeInstalledApps = !!this.auto_installed.length;
			this.needsToBeShown = this._showToBeInstalledApps || this._chooseHostsNeedsToBeShown;
			return pages;
		},

		isPageVisible: function(pageName) {
			switch (pageName) {
				case 'appsOverview':
					return this._showToBeInstalledApps;
					break;
				case 'chooseHosts':
					return this._chooseHostsNeedsToBeShown;
					break;
				default:
					return true;
			}
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



