/*
 * Copyright 2011-2014 Univention GmbH
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
	"dojo/when",
	"dojo/_base/lang",
	"put-selector/put",
	"umc/app",
	"umc/tools",
	"umc/widgets/TitlePane"
], function(when, lang, put, app, tools, TitlePane) {

	var load_first_steps = function(){
		var app = tools.umcpCommand('appcenter/get', {'application': 'owncloud82'}).then(function(data) {
			return data.result;
		});
		when(app).then(lang.hitch(this, function(loadedApp) {
			if (loadedApp === null) {
				console.warn('Error: Empty response');
			}
			var readme_as_html = put('div', {
				innerHTML: loadedApp.readme
			});
			var detailsPane = new TitlePane({
				title: "First Steps",
				content: readme_as_html
			});
			var overviewNode = document.getElementsByClassName("umcOverviewPane")[0];
			put(overviewNode, '-', detailsPane.domNode);
		}));
	};
	load_first_steps();
	return null;
});
