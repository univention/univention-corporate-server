/*
 * Copyright 2013 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/dom-construct",
	"dojo/dom-style",
	"dojo/topic",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Module",
	"umc/modules/appcenter/AppCenterPage",
	"umc/i18n!umc/modules/appcenter",
	"umc/i18n!umc/modules/apps"
], function(declare, lang, kernel, domConstruct, domStyle, topic, tools, TitlePane, Text, ConfirmDialog, ContainerWidget, Page, Module, AppCenterPage, appCenterTranslate, _) {
	// behaves like a button, but it is a simple <a>-tag
	//   needs a parentWidget to connect the onclick-event to
	//   callbackId should be unique within this parentWidget (css-class)
	var _AnchorButton = function(content, callbackId, parentWidget, callback) {
		var anchor = domConstruct.create('a', {
			href: 'javascript:void(0)',
			'class': callbackId,
			innerHTML: content
		});
		parentWidget.on('.' + callbackId + ':click', function() {
			callback(callbackId);
		});
		return anchor;
	};

	return declare("umc.modules.apps", Module, {
		// hide page completely while loading. otherwise a <title missing> is shown
		standbyOpacity: 1,

		buildRendering: function() {
			this.inherited(arguments);
			// use many functions from the app center.
			// dont render it directly
			this._appcenterPage = new AppCenterPage({
				standby: lang.hitch(this, 'standby'),
				autoStart: false,
				showModuleUsage: true,
				updateApplications: lang.hitch(this, function() {
					this.updateApplication();
				})
			});
			this._appcenterPage._grid.categoriesDisplayed = false; // dont show categories in app center icon (can go beyond title pane)
			this.own(this._appcenterPage);
			var buttons = [{
				name: 'close',
				label: _('Close'),
				align: 'left',
				callback: lang.hitch( this, function() {
					topic.publish('/umc/tabs/close', this);
				})
			}];
			this._page = new Page({
				footerButtons: buttons
			});
			this.addChild(this._page);
			this._container = null;
			this.updateApplication();
		},

		updateApplication: function() {
			if (this._container) {
				this._page.removeChild(this._container);
				this._container.destroyRecursive();
			}
			this._container = new ContainerWidget({
				scrollable: true
			});
			this._page.addChild(this._container);

			this._table = domConstruct.create('table', {
				style: {width: '500px'}
			});
			this._detailsPane = new TitlePane({
				title: _('Details'),
				content: this._table
			});
			this._container.addChild(this._detailsPane);

			this._usageText = new Text({});
			this._usagePane = new TitlePane({
				title: appCenterTranslate('Notes on using'),
				content: this._usageText
			});
			this._container.addChild(this._usagePane);

			this._descriptionText = new Text({});
			var descriptionPane = new TitlePane({
				title: _('Description'),
				content: this._descriptionText
			});
			this._container.addChild(descriptionPane);

			this.standby(true);
			tools.umcpCommand('apps/get', {}, undefined, this.moduleFlavor).then(lang.hitch(this, function(data) {
				var app = data.result;
				if (app === null) {
					// no app found. should not happen if not opened manually
					topic.publish('/umc/tabs/close', this);
					return;
				}
				this._page.set('headerText', app.name);

				// show appcenter-icon to the left of the table
				var iconDiv = domConstruct.create('div', {'class': 'umcGalleryPane'});
				var appIcon = this._appcenterPage._grid.renderRow(lang.mixin({}, app, {description: null})); // no tooltip
				domStyle.set(appIcon, 'cursor', 'default'); // without hover effects (as clicking on it does not open any dialog)
				domStyle.set(appIcon, 'backgroundColor', 'inherit');
				domConstruct.place(appIcon, iconDiv, 'only');
				domConstruct.place(iconDiv, this._table, 'before');

				// adding a row to the table per detail
				// use just the keys and values as in the app center detail dialog
				this.addToDetails(appCenterTranslate('Vendor'), this._appcenterPage._detail_field_custom_vendor(app));
				this.addToDetails(appCenterTranslate('Maintainer'), this._appcenterPage._detail_field_custom_maintainer(app));
				this.addToDetails(appCenterTranslate('Contact'), this._appcenterPage._detail_field_custom_contact(app));
				this.addToDetails(appCenterTranslate('Website'), this._appcenterPage._detail_field_custom_website(app));
				this.addToDetails(appCenterTranslate('Installed version'), this._appcenterPage._detail_field_custom_version(app));
				this.addToDetails('', '&nbsp;');
				if (app.candidate_version) {
					var candidate_version = app.candidate_version;
					if (app.allows_using && app.can_update) {
						var upgradeButton = _AnchorButton(
							candidate_version,
							'upgrade',
							this._detailsPane,
							lang.hitch(this, function() {
								var confirmDialog = new ConfirmDialog({
									title: _('Upgrade %s', app.name),
									message: '<strong>' + _('Do you really want to upgrade to %s?', app.candidate_version) + '</strong>',
									options: [{
										label: _('No'),
										name: 'no',
										'default': true
									}, {
										label: _('Yes'),
										name: 'yes'
									}]
								});
								confirmDialog.on('confirm', lang.hitch(this, function(answer) {
									confirmDialog.close();
									if (answer == 'yes') {
										this._appcenterPage.upgradeApp(app);
									}
								}));
								confirmDialog.show();
							})
						);
						candidate_version = upgradeButton.outerHTML;
					}
					this.addToDetails(appCenterTranslate('Candidate version'), candidate_version);
				}
				this.addToDetails(appCenterTranslate('Upgrade not possible'), this._appcenterPage._detail_field_custom_cannot_update_reason(app));

				if (app.can_uninstall) {
					var uninstallButton = _AnchorButton(
						_('Uninstall %s', app.name),
						'uninstall',
						this._detailsPane,
						lang.hitch(this, function() {
							this._appcenterPage._call_installer('uninstall', app);
						})
					);
					this.addToDetails(appCenterTranslate('Uninstall'), uninstallButton.outerHTML);
				}

				var locale = kernel.locale.slice( 0, 2 ).toLowerCase();
				var usage = app['readme_' + locale] || app.readme_en;
				if (usage) {
					usage = lang.replace(usage, app);
				} else {
					usage = this._appcenterPage._detail_field_custom_usage(app);
				}
				if (usage) {
					this._usageText.set('content', usage);
				} else {
					this._container.removeChild(this._usagePane);
					this._usagePane.destroyRecursive();
				}

				this._descriptionText.set('content', this._appcenterPage.formatTxt(app.longdescription));
				this.standby(false);
			}),
			lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		addToDetails: function(key, value) {
			if (! value) {
				return;
			}
			var tr = domConstruct.create('tr', {}, this._table);
			domConstruct.create('td', {innerHTML: key}, tr);
			domConstruct.create('td', {innerHTML: value}, tr);
		}

	});
});

