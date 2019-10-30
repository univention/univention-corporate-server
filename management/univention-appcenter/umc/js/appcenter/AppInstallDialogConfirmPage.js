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
	"dojo/_base/array",
	"dojo/dom-construct",
	"dijit/layout/ContentPane",
	"umc/tools",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, domConstruct, ContentPane, tools, Text, _) {
	return {
		getPageConf: function(mainInfo, dependenciesInfo, host) {

			var grid = domConstruct.create('div', {
				'class': 'appIconAndNameGrid'
			});
			var allInfo = [mainInfo].concat(dependenciesInfo);
			array.forEach(allInfo, function(info) {
				domConstruct.create('div', {
					'class': 'appIconAndNameGrid__icon ' + tools.getIconClass(info.app.logoName, 'scalable'),
				}, grid);
				domConstruct.create('div', {
					innerHTML: info.app.name
				}, grid);
			});

			var headerText = _('Installation of %s', mainInfo.app.name);

			var isRemoteAction = host && tools.status('hostname') != host;
			var helpText = _('Please confirm to install the application %s on this host.', mainInfo.app.name);
			if (isRemoteAction) {
				helpText = _('Please confirm to install the application %(name)s on host %(host)s.', {name: mainInfo.app.name, host: host});
			}
			if (dependenciesInfo.length) {
				helpText = _('Please confirm to install these applications on this host.');
				if (isRemoteAction) {
					helpText = _('Please confirm to install these applications on host %(host)s.', {host: host});
				}
			}

			return {
				name: 'confirm',
				headerText: headerText,
				widgets: [{
					type: Text,
					name: 'confirm_helpText',
					content: helpText,
				}, {
					type: ContentPane,
					'class': 'appIconAndNameGridWrapper',
					name: 'confirm_grid',
					content: grid,
					visible: dependenciesInfo.length
				}]
			};
		}
	};
});




