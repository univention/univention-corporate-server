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
	"./AppInstallWizardLicenseAgreementPage",
	"./AppInstallWizardReadmeInstallPage",
	"./AppInstallWizardAppSettingsPage",
	"put-selector/put",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, domClass, on, entities, ContentPane, ContainerWidget, Text, Wizard, AppText,
		AppDetailsContainer, LicenseAgreementPage, ReadmeInstallPage, AppSettingsPage, put, _) {
	return declare('umc.modules.appcenter.AppInstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',

		_appDetailsContainer: null,

		// these properties have to be provided
		apps: null,
		appSettings: null,
		dryRunResults: null,
		action: null,

		needsToBeShown: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._hasErrors = Object.values(this.dryRunResults).some(details =>
				!!Object.keys(details.invokation_forbidden_details).length ||
					!!Object.keys(details.broken).length
			);
			this.pages = [];
			this._addPages();
		},

		_addPages: function() {
			this._addDetailsPage('warnings', '');
			this._addLicenseAgreementPages();
			this._addReadmeInstallPages();
			this._addDetailsPage('details', _('Package changes'));
			this._addAppSettingsPages();
		},

		_addDetailsPage: function(name, helpText) {
		 	const page = {
				name: name,
				'class': 'appInstallWizard__detailsPage',
				headerText: '',
				helpText: helpText,
				widgets: [{
					type: ContainerWidget,
					name: `${name}_container`,
					size: 'Two',
				}]
		 	};
			this.pages.push(page);
		},

		_funcLabelStart() {
			switch (this.action) {
				case 'remove':
					return _('Start removal');
				case 'upgrade':
					return _('Start upgrade');
				default:
					return _('Start installation');
			}
		},

		_funcLabelStartAnyway() {
			switch (this.action) {
				case 'remove':
					return _('Start removal anyway');
				case 'upgrade':
					return _('Start upgrade anyway');
				default:
					return _('Start installation anyway');
			}
		},

		_funcLabelStartWithLicense() {
			switch (this.action) {
				case 'remove':
					return _('Accept license and start removal');
				case 'upgrade':
					return _('Accept license and start upgrade');
				default:
					return _('Accept license and start installation');
			}
		},

		_hidrateDetailPage: function(isWarning) {
			const pageName = isWarning ? 'warnings' : 'details';
			const containerName = isWarning ? 'warnings_container' : 'details_container';
			const container = this.getWidget(pageName, containerName);

			const order = ['__all__', ...this.apps.map(app => app.id)];
			const keys = Object.keys(this.dryRunResults);
			const final = [];
			for (const appId of order) {
				final.push(...keys.filter(key => key.startsWith(appId + '$$')));
			}
			for (const key of final) {
				const details = this.dryRunResults[key];
				const detailsContainer = new AppDetailsContainer({
					funcName: this.action,
					funcLabel: this._funcLabelStart(),
					app: details.app,
					details,
					host: details.host,
					showWarnings: isWarning,
					showNonWarnings: !isWarning,
				});
				if (!detailsContainer.doesShowSomething) {
					detailsContainer.destroyRecursive();
					continue;
				}

				const card = new ContainerWidget({
					'class': 'umcCard2 umcAppDetailsContainerCard'
				});
				const header = put(card.containerNode, 'div.umcAppDetailsContainerCard__header');
				if (details.app.id === '__all__') {
					put(header, 'span.umcAppDetailsContainerCard__header__main.umcAppDetailsContainerCard__header__host', entities.encode(details.host));
				} else {
					const appText = new AppText({
						'class': 'umcAppDetailsContainerCard__header__main umcAppDetailsContainerCard__header__appText',
						app: AppText.appFromApp(details.app),
					});
					card.own(appText);
					put(header, appText.domNode);
					put(header, 'span.umcAppDetailsContainerCard__header__secondary.umcAppDetailsContainerCard__header__host', entities.encode(details.host));
				}
				card.addChild(detailsContainer);
				container.addChild(card);

				on(detailsContainer, 'solutionClicked', lang.hitch(this, 'onSolutionClicked'));
			}
			this.getPage(pageName).set('visible', container.hasChildren());
		},

		_addLicenseAgreementPages: function() {
			if (this.action !== 'install') {
				return;
			}
			for (const app of this.apps) {
				const pageConf = LicenseAgreementPage.getPageConf(app);
				if (pageConf) {
					this.pages.push(pageConf);
				}
			}
		},

		_addReadmeInstallPages: function() {
			for (const app of this.apps) {
				let readmeAttr;
				if (this.action === 'upgrade') {
					readmeAttr = 'candidateReadmeUpdate';
				} else if (this.action === 'remove') {
					readmeAttr = 'readmeUninstall';
				} else {
					readmeAttr = 'readmeInstall';
				}
				const pageConf = ReadmeInstallPage.getPageConf(app, readmeAttr);
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

			this._hidrateDetailPage(true);
			this._hidrateDetailPage(false);

			const visiblePages = this.pages
				.filter(page => this.isPageVisible(page.name))
				.map(page => this.getPage(page.name));
			this.needsToBeShown = !!visiblePages.length;

			if (this.action === 'install') {
				const headerText = this.apps.length === 1
					? _('Installation of %s', this.apps[0].name)
					: _('Installation of multiple apps');
				visiblePages.forEach(function(page) {
					page.set('headerText', headerText);
				});
			} else if (this.action === 'upgrade') {
				const headerText = this.apps.length === 1
					? _('Upgrade of %s', this.apps[0].name)
					: _('Upgrade of multiple apps');
				visiblePages.forEach(function(page) {
					page.set('headerText', headerText);
				});
			} else {
				const headerText = this.apps.length === 1
					? _('Removal of %s', this.apps[0].name)
					: _('Removal of multiple apps');
				visiblePages.forEach(function(page) {
					page.set('headerText', headerText);
				});
			}

			if (this.isPageVisible('warnings')) {
				if (this._hasErrors) {
					this.getPage('warnings').set('helpText', _('We cannot continue. Please refer to the information below to solve the problem and try again.'));
				} else {
					this.getPage('warnings').set('helpText', _('We detected some problems that may lead to a errors later. Please consider the information below before continuing.'));
				}
			}
		},

		isPageVisible: function(pageName) {
			switch (pageName) {
				case 'warnings':
				case 'details':
					return this.getPage(pageName).get('visible');
				default:
					return true;
			}
		},

		next: function(pageName) {
			let next = this.inherited(arguments);
			if (pageName && pageName.startsWith('appSettings_')) {
				const page = this.getPage(pageName);
				const appSettingsForm = this.getWidget(pageName, page.$appSettingsFormName);
				if (!appSettingsForm.validate()) {
					appSettingsForm.focusFirstInvalidWidget();
					next = pageName;
				}
			}
			return next;
		},

		getFooterButtons: function(pageName) {
			const buttons = this.inherited(arguments);
			if (pageName === 'warnings') {
				array.forEach(buttons, (button) => {
					if (button.name === 'next') {
						button.label = _('Continue anyway');
					}
					if (button.name === 'finish') {
						button.label = this._funcLabelStartAnyway();
					}
				});
			} else if (pageName.startsWith('licenseAgreement_')) {
				buttons.forEach((button) => {
					if (button.name === 'next') {
						button.label = _('Accept license');
					}
					if (button.name === 'finish') {
						button.label = this._funcLabelStartWithLicense();
					}
				});
			} else {
				array.forEach(buttons, (button) => {
					if (button.name === 'finish') {
						button.label = this._funcLabelStart();
					}
				});
			}
			return buttons;
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			if (pageName === 'warnings') {
				const buttons = this._pages[pageName]._footerButtons;
				if (this._hasErrors) {
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



