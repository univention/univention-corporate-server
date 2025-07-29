/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
