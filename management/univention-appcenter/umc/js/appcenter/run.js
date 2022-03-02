/*
 * Copyright 2011-2022 Univention GmbH
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

define([
	"dojo/_base/lang",
	"dojo/promise/all",
	"dojo/topic",
	"umc/tools",
	"umc/app",
	"umc/widgets/ProgressBar",
	"umc/modules/appcenter/AppInstallDialog",
	"umc/i18n!umc/modules/appcenter",
], function(lang, all, topic, tools, UMC, ProgressBar, AppInstallDialog, _) {
	return {
		subscribe: function(module) {
			module.own(topic.subscribe('/appcenter/run/install', (apps, hosts, suggested, page) => {
				if (module.moduleID !== page.moduleID || module.moduleFlavor !== page.moduleFlavor) {
					return;
				}
				this.run(module, 'install', apps, hosts, page);
			}));
			module.own(topic.subscribe('/appcenter/run/upgrade', (apps, hosts, suggested, page) => {
				if (module.moduleID !== page.moduleID || module.moduleFlavor !== page.moduleFlavor) {
					return;
				}
				this.run(module, 'upgrade', apps, hosts, page);
			}));
			module.own(topic.subscribe('/appcenter/run/remove', (apps, hosts, suggested, page) => {
				if (module.moduleID !== page.moduleID || module.moduleFlavor !== page.moduleFlavor) {
					return;
				}
				this.run(module, 'remove', apps, hosts, page);
			}));
		},

		run: function(module, action, apps, hosts, page) {
			var installDialog = new AppInstallDialog({
				moduleID: module.moduleID,
				moduleFlavor: module.moduleFlavor,
				standbyDuring: lang.hitch(module, 'standbyDuring')
			});
			module.addChild(installDialog);
			module.selectChild(installDialog);
			installDialog.startAction(action, apps, hosts).then(
				() => {
					this.afterRun(
						lang.hitch(module, 'standbyDuring'),
						page)
					.then(() => {
						module.selectChild(page);
						module.removeChild(installDialog);
					});
				}, () => {
					module.selectChild(page);
					module.removeChild(installDialog);
				}
			);
		},

		afterRun: function(standbyDuring, page) {
			// update the list of apps
			var deferred = tools.renewSession().then(() => {
				var reloadPage = page.reloadPage();
				var reloadModules = UMC.reloadModules();
				return all([reloadPage, reloadModules]).then(function() {
					tools.checkReloadRequired();
				});
			});

			// show standby animation
			var progressBar = new ProgressBar({});
			progressBar.reset();
			progressBar.setInfo(_('Updating session and module data...'), '', Infinity);
			return standbyDuring(deferred, progressBar);
		},
	};
});
