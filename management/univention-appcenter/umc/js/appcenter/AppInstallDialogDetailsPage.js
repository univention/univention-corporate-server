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
	"dojo/dom-construct",
	"dijit/layout/ContentPane",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"put-selector/put",
	"./AppDetailsContainer",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, domConstruct, ContentPane, tools, Text, ComboBox, put, AppDetailsContainer, _) {
	return {
		getPageConf: function(info, isMainInfo, isMultiAppInstall, host, appDetailsPage) {
			var grid = domConstruct.create('div', {
				'class': 'appIconAndNameGrid'
			});
			domConstruct.create('div', {
				'class': 'appIconAndNameGrid__icon ' + tools.getIconClass(info.app.logoName, 'scalable'),
			}, grid);
			domConstruct.create('div', {
				innerHTML: info.app.name
			}, grid);

			var headerText = '';
			if (isMainInfo) {
				headerText = _('Installation of %s', info.app.name);
			} else {
				headerText = _('Installation of dependency');
			}

			var name = lang.replace('details_{0}', [info.app.id]);
			return {
				name: name,
				headerText: headerText,
				widgets: [{
					type: ContentPane,
					'class': 'appIconAndNameGridWrapper',
					name: lang.replace('{0}_grid', [name]),
					content: grid,
					visible: isMultiAppInstall
				}, {
					type: ContentPane,
					'class': 'appInstallDialog__readme',
					name: lang.replace('{0}_details', [name]),
					// content: will be set in AppInstallWizard
				}]
			};
		}
	};
});






