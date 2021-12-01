/*
 * Copyright 2020-2021 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"dojox/html/entities",
	"dijit/layout/ContentPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Wizard",
	"./AppText",
	"./AppDetailsContainer",
	"./AppInstallWizardReadmeInstallPage",
	"put-selector/put",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, domClass, on, entities, ContentPane, ContainerWidget, Text, Wizard, AppText,
		AppDetailsContainer, ReadmeInstallPage, put, _) {
	return declare('umc.modules.appcenter.AppPostInstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',

		_appDetailsContainer: null,

		// these properties have to be provided
		apps: null,
		result: null,
		errorMessages: null,
		action: null,

		needsToBeShown: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = [];
			this._successApps = [];
			this.hasErrors = false;
			this._addPages();
		},

		_addPages: function() {
			this._addErrorPage();
			this._addReadmeInstallPages();
		},

		_addErrorPage() {
			// results are:
			// {hostname:
			//   {app:
			//     {success: true/false}
			//   },
			// },
			const brokenApps = [];
			for (const [hostname, appDetails] of Object.entries(this.result)) {
				for (const [appId, successDetails] of Object.entries(appDetails)) {
					if (!successDetails.success) {
						brokenApps.push([hostname, appId]);
					} else {
						this._successApps.push(appId);
					}
				}
			}
			if (brokenApps.length) {
				const failedAppsText = brokenApps.map(([host, app]) =>
					_("%s on %s", app, host)
				).join(", ");
				const pageConf = {
					name: 'failures',
					helpText: _('We tried to do as requested but failed for %s', failedAppsText),
					widgets: [{
						type: Text,
						style: 'display: block;',
						'class': 'AppDetailsDialog__warning AppDetailsDialog__warning--hard',
						name: 'failuresError',
						content: _('These are the error messages from the server. More information might be available on the system\'s logfile <em>/var/log/univention/appcenter.log</em>') + '<ul><li>' + this.errorMessages.join('</li><li>') + '</li></ul>',
					}]
				};
				this.pages.push(pageConf);
				this.hasErrors = true;
			}
		},

		_addReadmeInstallPages: function() {
			for (const app of this.apps) {
				if (!this._successApps.includes(app.id)) {
					continue;
				}
				let readmeAttr;
				if (this.action === 'upgrade') {
					readmeAttr = 'candidateReadmePostUpdate';
				} else if (this.action === 'remove') {
					readmeAttr = 'readmePostUninstall';
				} else {
					readmeAttr = 'readmePostInstall';
				}
				const pageConf = ReadmeInstallPage.getPageConf(app, readmeAttr);
				if (pageConf) {
					this.pages.push(pageConf);
				}
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			this.needsToBeShown = !!this.pages.length;

			if (this.action === 'install') {
				const headerText = this.apps.length === 1
					? _('Installation of %s', this.apps[0].name)
					: _('Installation of multiple Apps');
				this.pages.forEach((page) => {
					this.getPage(page.name).set('headerText', headerText)
				});
			} else if (this.action === 'upgrade') {
				const headerText = this.apps.length === 1
					? _('Upgrade of %s', this.apps[0].name)
					: _('Upgrade of multiple Apps');
				this.pages.forEach((page) => {
					this.getPage(page.name).set('headerText', headerText)
				});
			} else {
				const headerText = this.apps.length === 1
					? _('Removal of %s', this.apps[0].name)
					: _('Removal of multiple Apps');
				this.pages.forEach((page) => {
					this.getPage(page.name).set('headerText', headerText)
				});
			}
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			var buttons = this._pages[pageName]._footerButtons;
			if (!this.canFinish()) {
				if (buttons.finish) {
					domClass.add(buttons.finish.domNode, 'dijitDisplayNone');
				}
			}
			if (!this.canCancel()) {
				if (buttons.cancel) {
					domClass.add(buttons.cancel.domNode, 'dijitDisplayNone');
				}
			}
		},

		canFinish: function() {
			return !this.hasErrors;
		},

		canCancel: function() {
			return !this.canFinish();
		},
	});
});



