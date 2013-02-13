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
/*global define require console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/dom-construct",
	"dojo/topic",
	"umc/tools",
	"umc/widgets/Button",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Module",
	"umc/modules/appcenter/AppCenterPage",
	"umc/i18n!umc/modules/appcenter",
	"umc/i18n!umc/modules/apps"
], function(declare, lang, kernel, domConstruct, topic, tools, Button, TitlePane, Text, ContainerWidget, Page, Module, AppCenterPage, appCenterTranslate, _) {
	return declare("umc.modules.apps", Module, {
		standbyOpacity: 1,

		buildRendering: function() {
			this.inherited(arguments);
			this._appcenterPage = AppCenterPage();
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
			var container = new ContainerWidget({
				scrollable: true
			});
			this._page.addChild(container);

			this._table = domConstruct.create('table', {
				style: {width: '500px'}
			});
			var detailsPane = new TitlePane({
				title: _('Details'),
				content: this._table
			});
			container.addChild(detailsPane);

			this._text = new Text({});
			var descriptionPane = new TitlePane({
				title: _('Description'),
				content: this._text
			});
			container.addChild(descriptionPane);

			this.standby(true);
			tools.umcpCommand('apps/get', {'application' : this.moduleFlavor}).then(lang.hitch(this, function(data) {
				var app = data.result;
				if (app === null) {
					topic.publish('/umc/tabs/close', this);
					return;
				}
				this._page.set('headerText', app.name);

				this.addToDetails(appCenterTranslate('Vendor'), this._appcenterPage._detail_field_custom_vendor(app));
				this.addToDetails(appCenterTranslate('Maintainer'), this._appcenterPage._detail_field_custom_maintainer(app));
				this.addToDetails(appCenterTranslate('Contact'), this._appcenterPage._detail_field_custom_contact(app));
				this.addToDetails(appCenterTranslate('Website'), this._appcenterPage._detail_field_custom_website(app));
				this.addToDetails(appCenterTranslate('Version'), app.version);
				if (app.candidate_version) {
					var candidate_version = app.candidate_version;
					if (app.allows_using && app.can_update) {
						candidate_version = _('Upgrade to %s', candidate_version);
						var candidate_version_button = new Button({
							name: 'update',
							defaultButton: true,
							label: candidate_version,
							callback: lang.hitch(this, function() {
								this._appcenterPage.upgradeApp(app);
							})
						});
						this.own(candidate_version_button);
						candidate_version = candidate_version_button.domNode.outerHTML;
					}
					this.addToDetails(appCenterTranslate('Candidate version'), candidate_version);
				}
				this.addToDetails(appCenterTranslate('Upgrade not possible'), this._appcenterPage._detail_field_custom_cannot_update_reason(app));

				var locale = kernel.locale.slice( 0, 2 ).toLowerCase();
				var content = app['readme_' + locale] || app.readme_en;
				if (!content) {
					content = this._appcenterPage.formatTxt(app.longdescription);
				}
				this._text.set('content', content);
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

