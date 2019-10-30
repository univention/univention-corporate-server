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
	"dojo/dom-construct",
	"dijit/layout/ContentPane",
	"umc/tools",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, domConstruct, ContentPane, tools, Text, _) {
	return {
		getPageConf: function(app, isMultiAppInstall) {
			if (!app.readmePostInstall) {
				return null;
			}

			var grid = domConstruct.create('div', {
				'class': 'appIconAndNameGrid'
			});
			domConstruct.create('div', {
				'class': 'appIconAndNameGrid__icon ' + tools.getIconClass(app.logoName, 'scalable'),
			}, grid);
			domConstruct.create('div', {
				innerHTML: app.name
			}, grid);

			var name = lang.replace('readmePostInstall_{0}', [app.id]);
			return {
				name: name,
				headerText: _('Install information'),
				widgets: [{
					type: ContentPane,
					'class': 'appIconAndNameGridWrapper',
					name: lang.replace('{0}_grid', [name]),
					content: grid,
					visible: isMultiAppInstall
				}, {
					type: Text,
					'class': 'appInstallDialog__readmeTitle',
					name: lang.replace('{0}__subTitle'),
					content: _('Install information')
				}, {
					type: Text,
					'class': 'appInstallDialog__readme',
					name: lang.replace('{0}_readmePostInstall', [name]),
					content: app.readmePostInstall
				}]
			};
		}
	};
});





