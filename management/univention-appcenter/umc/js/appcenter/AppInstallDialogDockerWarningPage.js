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
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, domConstruct, ContentPane, tools, Text, CheckBox, _) {
	return {
		getPageConf: function(app, dependencies, appcenterDockerSeen) {
			if (appcenterDockerSeen) {
				return null;
			}

			var apps = [app].concat(dependencies);
			var dockerApps = apps.filter(function(app) {
				return app.installsAsDocker();
			});

			if (dockerApps.length === 0) {
				return null;
			}

			var grid = domConstruct.create('div', {
				'class': 'appIconAndNameGrid'
			});
			array.forEach(dockerApps, function(app) {
				domConstruct.create('div', {
					'class': 'appIconAndNameGrid__icon ' + tools.getIconClass(app.logoName, 'scalable'),
				}, grid);
				domConstruct.create('div', {
					innerHTML: app.name
				}, grid);
			});

			var text = '<p>' + _('This App uses a container technology. Containers have to be downloaded once. After that they can be used multiple times.') + '</p>' +
					'<p>' + _('Depending on your internet connection and on your server performance, the download and the App installation may take up to 15 minutes') + '</p>';
			if (dependencies.length) {
				text = '<p>' + _('The following Apps use a container technology. Containers have to be downloaded once. After that they can be used multiple times.') + '</p>' +
						'<p>' + _('Depending on your internet connection and on your server performance, the download and the App installation may take up to 15 minutes') + '</p>';
			}

			return {
				name: 'dockerWarning',
				headerText: _('Installation of %s', app.name),
				widgets: [{
					type: Text,
					name: 'dockerWarning_text',
					content: text
				}, { 
					type: ContentPane,
					'class': 'appIconAndNameGridWrapper',
					name: 'dockerWarning_grid',
					content: grid,
					visible: !!dependencies.length
				}, {
					type: CheckBox,
					name: 'dockerWarning_doNotShowAgain',
					label: _("Do not show this message again")
				}]
			};
		}
	};
});



