/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2013-2022 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"dojo/when",
	"dojo/promise/all",
	"umc/widgets/Module",
	"umc/modules/appcenter/run",
	"umc/modules/appcenter/AppDetailsPage",
	"umc/modules/appcenter/AppConfigDialog",
	"umc/modules/appcenter/AppDetailsDialog",
	"umc/i18n!umc/modules/apps"
], function(declare, lang, topic, when, all, Module, run, AppDetailsPage, AppConfigDialog, AppDetailsDialog, _) {
	return declare("umc.modules.apps", Module, {
		buildRendering: function() {
			this.inherited(arguments);

			var detailsDialog = new AppDetailsDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			var configDialog = new AppConfigDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			var appDetailsPage = new AppDetailsPage({
				app: {id: this.moduleFlavor},
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				backLabel: _('Close'),
				getAppCommand: 'apps/get',
				detailsDialog: detailsDialog,
				configDialog: configDialog,
				udmAccessible: this.udmAccessible(),
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});

			this.own(
				detailsDialog.on('showUp', lang.hitch(this, 'selectChild', detailsDialog)),
				configDialog.on('showUp', lang.hitch(this, 'selectChild', configDialog)),
				appDetailsPage.on('back', lang.hitch(this, function() {
					topic.publish('/umc/tabs/close', this);
				})),
				detailsDialog.on('back', lang.hitch(this, 'selectChild', appDetailsPage)),
				configDialog.on('back', lang.hitch(this, function(applied) {
					var loadPage = true;
					if (applied) {
						loadPage = all([appDetailsPage.reloadPage()]);
						this.standbyDuring(loadPage);
					}
					when(loadPage).then(lang.hitch(this, function() {
						this.selectChild(appDetailsPage);
					}));
				})),
				configDialog.on('update', lang.hitch(this, function() {
					var loadPage = all([appDetailsPage.reloadPage()]);
					loadPage = loadPage.then(lang.hitch(this, function() {
						configDialog.showUp();
					}));
					this.standbyDuring(loadPage);
				}))
			);

			run.subscribe(this);

			this.addChild(detailsDialog);
			this.addChild(configDialog);
			this.addChild(appDetailsPage);

			this.standbyDuring(appDetailsPage.appLoadingDeferred);
			this.selectChild(appDetailsPage);
		},

		udmAccessible: function() {
			// FIXME: this is a synchronous call and can
			// potentially fail although the module would
			// be loaded later on. this may not be of any
			// importance but it would be much cleaner
			// to extract the moduleInstalled('udm')
			// functionality from App to tools or
			// a dedicated module
			var udmAccessible = false;
			try {
				require('umc/modules/udm');
				udmAccessible = true;
			} catch(e) {
			}
			return udmAccessible;
		}
	});
});

