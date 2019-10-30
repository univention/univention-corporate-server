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
	"./AppInstallDialogReadmePostInstallPage",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, Wizard, tools, ReadmePostInstallPage, _) {
	return declare('umc.modules.appcenter.AppInstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',
		autoHeight: true,

		apps: null,
		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = this.getPages(this.apps);
		},

		getPages: function(apps) {
			var pages = [];
			var addedAppsCount = 0;
			var isMultiAppInstall = apps.length >= 2;
			apps.forEach(lang.hitch(this, function(app) {
				var wasAdded = this.addReadmePostInstallPage(app, isMultiAppInstall, pages);
				if (wasAdded) {
					addedAppsCount += 1;
				}
			}));
			// adjust headerText if multiple apps are in the wizard
			if (addedAppsCount >= 2) {
				var appIdx = 1;
				array.forEach(apps, lang.hitch(this, function(app) {
					var _pages = pages.filter(function(page) {
						return page.name.endsWith(lang.replace('_{0}', [app.id]));
					});
					if (_pages.length) {
						var headerText = _('Install information (%s/%s)', appIdx, addedAppsCount);
						_pages.forEach(function(page) {
							page.headerText = headerText;
						});
						appIdx += 1;
					}
				}));
			}
			return pages;
		},

		addReadmePostInstallPage: function(app, isMultiAppInstall, pages) {
			var pageConf = ReadmePostInstallPage.getPageConf(app, isMultiAppInstall);
			if (pageConf) {
				pages.push(pageConf);
			}
			return !!pageConf;
		}
	});
});



