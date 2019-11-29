/*
 * Copyright 2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/widgets/Wizard",
	"umc/tools",
	"./AppInstallDialogProblemsPage",
	"./AppInstallDialogLicenseAgreementPage",
	"./AppInstallDialogReadmeInstallPage",
	"./AppInstallDialogAppSettingsPage",
	"./AppInstallDialogDetailsPage",
	"./AppSettings",
	"./AppDetailsContainer",
	"./AppInstallDialogConfirmPage",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, Wizard, tools, ProblemsPage, LicenseAgreementPage, ReadmeInstallPage, AppSettingsPage, DetailsPage, AppSettings, AppDetailsContainer, ConfirmPage, _) {
	return declare('umc.modules.appcenter.AppInstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',
		autoHeight: true,

		appDetailsPage: null,
		installInfo: null,
		mainAppIdx: null,
		host: null,
		_mainInfo: null,
		_dependenciesInfo: null,
		_detailsContainers: null,

		constructor: function() {
			this.inherited(arguments);
			this._detailsContainers = {};
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._mainInfo = this.installInfo[this.mainAppIdx];
			this._dependenciesInfo = this.installInfo.filter(lang.hitch(this, function(info, idx) {
				return idx !== this.mainAppIdx;
			}));
			this.pages = this.getPages(this._mainInfo, this._dependenciesInfo, this.host, this.appDetailsPage);
		},

		getPages: function(mainInfo, dependenciesInfo, host, appDetailsPage) {
			var pages = [];
			var installationsWithSeriousProblems = this.installInfo.filter(function(info) {
				return info.details && info.details.serious_problems;
			});
			this._installationHasSeriousProblems = installationsWithSeriousProblems.length >= 1;
			if (this._installationHasSeriousProblems) {
				this.addProblemsPage(mainInfo, installationsWithSeriousProblems, pages);
				let addedDependenciesCount = 0;
				array.forEach(installationsWithSeriousProblems, lang.hitch(this, function(info) {
					var wasAdded = this.addDetailsPage(info, false, isMultiAppInstall, host, appDetailsPage, pages);
					if (wasAdded) {
						addedDependenciesCount += 1;
					}
				}));
				// adjust headerText if multiple apps are in the wizard
				let dependencyIdx = 1;
				array.forEach(installationsWithSeriousProblems, lang.hitch(this, function(info) {
					var _pages = pages.filter(function(page) {
						return page.name.endsWith(lang.replace('_{0}', [info.app.id]));
					});
					if (_pages.length) {
						var headerText = _('Result of pre-install checks (%s/%s)', dependencyIdx, addedDependenciesCount);
						_pages.forEach(function(page) {
							page.headerText = headerText;
						});
						dependencyIdx += 1;
					}
				}));
			} else {
				let addedDependenciesCount = 0;
				var isMultiAppInstall = dependenciesInfo.length >= 1;
				this.addLicenseAgreementPage(mainInfo, true, isMultiAppInstall, pages);
				this.addReadmeInstallPage(mainInfo, true, isMultiAppInstall, pages);
				this.addDetailsPage(mainInfo, true, isMultiAppInstall, host, appDetailsPage, pages);
				this.addAppSettingsPage(mainInfo, true, isMultiAppInstall, pages);
				array.forEach(dependenciesInfo, lang.hitch(this, function(info) {
					var wasAdded = false;
					wasAdded = this.addLicenseAgreementPage(info, false, isMultiAppInstall, pages) || wasAdded;
					wasAdded = this.addReadmeInstallPage(info, false, isMultiAppInstall, pages) || wasAdded;
					wasAdded = this.addDetailsPage(info, false, isMultiAppInstall, host, appDetailsPage, pages) || wasAdded;
					wasAdded = this.addAppSettingsPage(info, false, isMultiAppInstall, pages) || wasAdded;
					if (wasAdded) {
						addedDependenciesCount += 1;
					}
				}));
				// adjust headerText if multiple apps are in the wizard
				if (addedDependenciesCount >= 2) {
					let dependencyIdx = 1;
					array.forEach(dependenciesInfo, lang.hitch(this, function(info) {
						var _pages = pages.filter(function(page) {
							return page.name.endsWith(lang.replace('_{0}', [info.app.id]));
						});
						if (_pages.length) {
							var headerText = _('Installation of dependencies (%s/%s)', dependencyIdx, addedDependenciesCount);
							_pages.forEach(function(page) {
								page.headerText = headerText;
							});
							dependencyIdx += 1;
						}
					}));
				}
				this.addConfirmPage(mainInfo, dependenciesInfo, host, pages);
			}
			return pages;
		},

		postCreate: function() {
			this.inherited(arguments);

			tools.forIn(this._detailsContainers, lang.hitch(this, function(appId, detailsContainer) {
				this.getWidget(lang.replace('details_{0}', [appId]), lang.replace('details_{0}_details', [appId])).set('content', detailsContainer);
			}));
		},

		addProblemsPage: function(mainInfo, infos, pages) {
			var pageConf = ProblemsPage.getPageConf(mainInfo, infos);
			pages.push(pageConf);
		},

		addLicenseAgreementPage: function(info, isMainInfo, isMultiAppInstall, pages) {
			var pageConf = LicenseAgreementPage.getPageConf(info, isMainInfo, isMultiAppInstall);
			if (pageConf) {
				pages.push(pageConf);
			}
			return !!pageConf;
		},

		addReadmeInstallPage: function(info, isMainInfo, isMultiAppInstall, pages) {
			var pageConf = ReadmeInstallPage.getPageConf(info, isMainInfo, isMultiAppInstall);
			if (pageConf) {
				pages.push(pageConf);
			}
			return !!pageConf;
		},

		addDetailsPage: function(info, isMainInfo, isMultiAppInstall, host, appDetailsPage, pages) {
			var detailsContainer = new AppDetailsContainer({
				app: info.app,
				funcName: 'install',
				funcLabel: _('Install'),
				details: info.details,
				host: this.host,
				appDetailsPage: this.appDetailsPage,
				onBack: lang.hitch(this, 'onBack')
			});
			if (!detailsContainer.doesShowSomething) {
				return false;
			}
			this._detailsContainers[info.app.id] = detailsContainer;
			var pageConf = DetailsPage.getPageConf(info, isMainInfo, isMultiAppInstall, host, appDetailsPage);
			pages.push(pageConf);
			return true;
		},

		addAppSettingsPage: function(info, isMainInfo, isMultiAppInstall, pages) {
			var pageConf = AppSettingsPage.getPageConf(info, isMainInfo, isMultiAppInstall);
			if (pageConf) {
				pages.push(pageConf);
			}
			return !!pageConf;
		},

		addConfirmPage: function(mainInfo, dependenciesInfo, host, pages) {
			var pageConf = ConfirmPage.getPageConf(mainInfo, dependenciesInfo, host);
			pages.push(pageConf);
		},

		getFooterButtons: function(pageName) {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, lang.hitch(this, function(button) {
				if (button.name === 'finish') {
					if (this._installationHasSeriousProblems) {
						button.label = _('Close');
					} else {
						button.label = this.installInfo.length === 1 ? _('Install app') : _('Install apps');
					}
				}
			}));
			if (pageName.startsWith('licenseAgreement')) {
				array.forEach(buttons, function(button) {
					if (button.name === 'next') {
						button.label = _('Accept license');
					}
				});
			}
			return buttons;
		}
	});
});


