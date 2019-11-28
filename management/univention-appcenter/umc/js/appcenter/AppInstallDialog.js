/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/dom-class",
	"dojo/topic",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"./AppPreinstallWizard",
	"./AppInstallWizard",
	"./AppPostInstallWizard",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, domClass, topic, tools, ContainerWidget, AppPreinstallWizard, AppInstallWizard, AppPostInstallWizard, _) {
	return declare("umc.modules.appcenter.AppInstallDialog", [ ContainerWidget ], {
		_preinstallWizard: null,
		_installWizard: null,

		_mainAppId: null,
		_installationHasSeriousProblems: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				label: _('Cancel installation'),
				callback: lang.hitch(this, 'cancelInstallation')
			}];
		},

		cancelInstallation: function() {
			if (!this._installationHasSeriousProblems) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this._mainAppId, 'user-cancel');
			}
			this.onBack();
		},

		cleanup: function() {
			this._installationHasSeriousProblems = false;
			if (this._preinstallWizard) {
				this._preinstallWizard.destroyRecursive();
			}
			if (this._installWizard) {
				this._installWizard.destroyRecursive();
			}
			if (this._postInstallWizard) {
				this._postInstallWizard.destroyRecursive();
			}
		},

		showPreinstallWizard: function(app, dependencies, appcenterDockerSeen, appDetailsPage) {
			this.cleanup();
			this._preinstallWizard = new AppPreinstallWizard({
				app: app,
				dependencies: dependencies,
				appcenterDockerSeen: appcenterDockerSeen
			});
			this._preinstallWizard.on('cancel', lang.hitch(this, 'cancelInstallation'));
			this._preinstallWizard.on('checksDone', lang.hitch(this, function(host, installInfo) {
				this.showInstallWizard(host, installInfo, appDetailsPage);
			}));
			this.addChild(this._preinstallWizard);
		},

		showInstallWizard: function(host, installInfo, appDetailsPage) {
			this.cleanup();
			this._installationHasSeriousProblems = installInfo.some(function(info) {
				return info.details && info.details.serious_problems;
			});
			if (this._installationHasSeriousProblems) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this._mainAppId, 'cannot-continue');
			}
			this._installWizard = new AppInstallWizard({
				host: host,
				installInfo: installInfo ,
				appDetailsPage: appDetailsPage,
				onBack: lang.hitch(this, 'onBack')
			});
			this._installWizard.on('cancel', lang.hitch(this, 'cancelInstallation'));
			this._installWizard.on('finished', lang.hitch(this, function(values) {
				if (appDetailsPage.fromSuggestionCategory) {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this._mainAppId, 'installFromSuggestion');
				} else {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this._mainAppId, 'install');
				}
				// TODO call backend install function
				// maybe adjust getValues() of AppInstallWizard
				// DIRK
				this.showPostInstallWizard(installInfo.map(function(info) { return info.app; }));
			}));
			this.addChild(this._installWizard);
		},

		showPostInstallWizard: function(apps) {
			this.cleanup();
			this._postInstallWizard = new AppPostInstallWizard({
				apps: apps
			});
			this._postInstallWizard.on('cancel', lang.hitch(this, 'onBack'));
			this._postInstallWizard.on('finished', lang.hitch(this, 'onBack'));
			this.addChild(this._postInstallWizard);
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppCenterDialog');
			domClass.add(this.domNode, 'umcAppInstallDialog');
			domClass.add(this.domNode, 'col-xs-12 col-sm-12 col-md-10 col-md-offset-1 col-lg-8 col-lg-offset-2');
		},

		showUp: function(app, dependencies, appcenterDockerSeen, appDetailsPage) {
			this._mainAppId = app.id;
			this.showPreinstallWizard(app, dependencies, appcenterDockerSeen, appDetailsPage);
			this.onShowUp();
			// this._continueDeferred.then(lang.hitch(this, 'onBack'), lang.hitch(this, 'onBack'));
			// return this._continueDeferred;
		},

		onShowUp: function() {

		},

		onBack: function() {

		},

		// for _registerAtParentOnShowEvents
		_onShow: function() {

		}
	});
});

