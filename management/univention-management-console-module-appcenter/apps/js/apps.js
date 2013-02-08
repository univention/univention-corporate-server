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
	"dojo/topic",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Module",
	"umc/i18n!umc/modules/apps" // not needed atm
], function(declare, lang, kernel, topic, tools, Text, ContainerWidget, Page, Module, _) {
	var formatTxt = function(txt) {
		// FIXME:
		// Same as in appcenter/AppCenterPage.js
		// Should go into tools.
		// do not allow HTML
		txt = txt.replace(/</g, '&lt;');
		txt = txt.replace(/>/g, '&gt;');

		// insert links
		txt = txt.replace(/(https?:\/\/\S*)/g, '<a target="_blank" href="$1">$1</a>');

		// format line breakes
		txt = txt.replace(/\n\n\n/g, '\n<br>\n<br>\n<br>\n');
		txt = txt.replace(/\n\n/g, '\n<br>\n<br>\n');

		return txt;
	};

	return declare("umc.modules.apps", Module, {
		standbyOpacity: 1,

		buildRendering: function() {
			this.inherited(arguments);
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
			this._text = new Text({});
			container.addChild(this._text);

			this.standby(true);
			tools.umcpCommand('apps/get', {'application' : this.moduleFlavor}).then(lang.hitch(this, function(data) {
				var app = data.result;
				if (app === null) {
					topic.publish('/umc/tabs/close', this);
					return;
				}
				this._page.set('headerText', app.name);
				var locale = kernel.locale.slice( 0, 2 ).toLowerCase();
				var content = app['readme_' + locale] || app.readme_en;
				if (!content) {
					var url = app.website || app.websitevendor;
					content = lang.replace(_('The maintainer did not provide a dedicated README for the application. See {url} for further details.'), {url: url});
					content += '\n\n' + app.longdescription;
					content = formatTxt(content);
				}
				this._text.set('content', content);
				this.standby(false);
			}),
			lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		startup: function() {
			this.inherited(arguments);
		}

	});
});

