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
	"dijit/layout/ContentPane",
	"umc/widgets/Wizard",
	"umc/widgets/Text",
	"./AppDetailsContainer",
	"./AppInstallWizardLicenseAgreementPage",
	"./AppInstallWizardReadmeInstallPage",
	"./AppInstallWizardAppSettingsPage",
	"put-selector/put",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, domClass, on, ContentPane, Wizard, Text, AppDetailsContainer, LicenseAgreementPage,
		ReadmeInstallPage, AppSettingsPage, put, _) {
	return declare('umc.modules.appcenter.AppInstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',

		_appDetailsContainer: null,

		// these properties have to be provided
		hosts: null,
		apps: null,
		appSettings: null,
		// dryRunResults: null,
		appDetailsPage: null,
		//

		needsToBeShown: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = [];
			this._addPages();
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppCenterInstallWizard');
		},

		_addPages: function() {
			// this._addDetailsPage('warnings', '');
			this._addLicenseAgreementPages();
			this._addReadmeInstallPages();
			// this._addDetailsPage('details', _('Package changes'));
			this._addAppSettingsPages();
		},

		_addDetailsPage: function(name, helpText) {
			this.pages.push({
				name: name,
				'class': 'appInstallWizard__detailsPage',
				headerText: '',
				helpText: helpText,
				widgets: [{
					type: ContentPane,
					name: name,
					size: 'Two'
				}]
			});
		},

		_hidrateDetailPage: function(name, showWarnings, showNonWarnings) {
			// TODO wenn trying to define an AppDetailsContainer with these properties in this.pages then Wizard.js throws errors.
			// take a closer look at that. For now we add the AppDetailsContainer(s) in postCreate
			var detailsContainer = new AppDetailsContainer({
				funcName: 'install',
				funcLabel: _('Install'),
				app: this.app,
				details: this.dryRunResults,
				host: this.host,
				appDetailsPage: this.appDetailsPage,
				showWarnings: showWarnings,
				showNonWarnings: showNonWarnings
			});
			on(detailsContainer, 'solutionClicked', lang.hitch(this, 'onSolutionClicked'));
			this.getWidget(name, name).set('content', detailsContainer);
			this.getPage(name).set('visible', detailsContainer.doesShowSomething);
		},

		_addLicenseAgreementPages: function() {
			for (const app of this.apps) {
				const pageConf = LicenseAgreementPage.getPageConf(app);
				if (pageConf) {
					this.pages.push(pageConf);
				}
			}
		},

		_addReadmeInstallPages: function() {
			for (const app of this.apps) {
				const pageConf = ReadmeInstallPage.getPageConf(app);
				if (pageConf) {
					this.pages.push(pageConf);
				}
			}
		},

		_addAppSettingsPages: function() {
			for (const app of this.apps) {
				const pageConf = AppSettingsPage.getPageConf(app, this.appSettings[app.id]);
				if (pageConf) {
					this.pages.push(pageConf);
				}
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			// this._hidrateDetailPage('warnings', true, false);
			// this._hidrateDetailPage('details', false, true);

			const visiblePages = this.pages
				.filter(page => this.isPageVisible(page.name))
				.map(page => this.getPage(page.name));
			this.needsToBeShown = !!visiblePages.length;

			var headerText = this.apps.length === 1
				? _('Installation of %s', this.apps[0].name)
				: _('Installation of multiple apps');
			// TODO
			// if (visiblePages.length === 1 || this.dryRunResults.serious_problems /* we can't get past the warnings page when serious_problems so no numbered headers */) {
			/*
			if (false) {
				visiblePages.forEach(function(page) {
					page.set('headerText', headerText);
				});
			} else {
				const licenseAgreementPages = visiblePages.filter(page => page.name.startsWith('licenseAgreement_'));
				for (let x = 0; x < licenseAgreementPages.length; x++) {
					const page = licenseAgreementPages[x];
					page.set('helpText', `${page.helpText} (${x+1}/${licenseAgreementPages.length})`);
				}
				const readmeInstallPages = visiblePages.filter(page => page.name.startsWith('readmeInstall_'));
				for (let x = 0; x < readmeInstallPages.length; x++) {
					const page = readmeInstallPages[x];
					page.set('helpText', `${page.helpText} (${x+1}/${readmeInstallPages.length})`);
				}
				const appSettingsPages = visiblePages.filter(page => page.name.startsWith('appSettings_'));
				for (let x = 0; x < appSettingsPages.length; x++) {
					const page = appSettingsPages[x];
					page.set('helpText', `${page.helpText} (${x+1}/${appSettingsPages.length})`);
				}
				const hideAppText = this.apps.length === 1;
				for (let x = 0; x < visiblePages.length; x++) {
					const page = visiblePages[x];
					page.set('headerText', lang.replace('{0} ({1}/{2})', [headerText, x+1, visiblePages.length]));
					if (hideAppText) {
						const appText = this.getWidget(page.name, 'appText');
						if (appText) {
							appText.set('visible', false);
						}

					}
				}
			}
			*/

			// TODO
			/*
			if (this.isPageVisible('warnings')) {
				if (this.dryRunResults.serious_problems) {
					this.getPage('warnings').set('helpText', _('The installation cannot be performed. Please refer to the information below to solve the problem and try again.'));
				} else {
					this.getPage('warnings').set('helpText', _('We detected some problems that may lead to a faulty installation. Please consider the information below before continuing with the installation.'));
				}
			}
			*/
		},

		isPageVisible: function(pageName) {
			// TODO startswith
			switch (pageName) {
				case 'warnings':
				case 'details':
					return this.getPage(pageName).get('visible');
				default:
					return true;
			}
		},

		next: function(pageName) {
			var next = this.inherited(arguments);
			// TODO startsWith
			switch (pageName) {
				case 'appSettings':
					var appSettingsForm = this.getWidget('appSettings', 'appSettings_appSettings');
					if (!appSettingsForm.validate()) {
						appSettingsForm.focusFirstInvalidWidget();
						next = pageName;
					}
					break;
			}
			return next;
		},

		getFooterButtons: function(pageName) {
			var buttons = this.inherited(arguments);
			if (pageName === 'warnings') {
				array.forEach(buttons, function(button) {
					if (button.name === 'next') {
						button.label = _('Continue anyway');
					}
					if (button.name === 'finish') {
						button.label = _('Install anyway');
					}
				});
			} else if (pageName.startsWith('licenseAgreement_')) {
				array.forEach(buttons, function(button) {
					if (button.name === 'next') {
						button.label = _('Accept license');
					}
					if (button.name === 'finish') {
						button.label = _('Accept license and install app');
					}
				});
			} else {
				array.forEach(buttons, lang.hitch(this, function(button) {
					if (button.name === 'finish') {
						button.label = _('Install app');
					}
				}));
			}
			return buttons;
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			if (pageName === 'warnings') {
				var buttons = this._pages[pageName]._footerButtons;
				if (this.dryRunResults.serious_problems) {
					if (buttons.next) {
						domClass.add(buttons.next.domNode, 'dijitDisplayNone');
					}
					if (buttons.finish) {
						domClass.add(buttons.finish.domNode, 'dijitDisplayNone');
					}
					if (buttons.previous) {
						domClass.add(buttons.previous.domNode, 'dijitDisplayNone');
					}
				}
			}
		},

		onSolutionClicked: function(stayAfterSolution) {
			// event stub
		}
	});
});



