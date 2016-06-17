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
	"dojo/dom-class",
	"dojo/_base/lang",
	"dojo/topic",
	"put-selector/put",
	"umc/app",
	"umc/tools",
	"umc/widgets/TitlePane"
], function(when, domClass, lang, topic, put, app, tools, TitlePane) {

	var detailsPane = null
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
			detailsPane = new TitlePane({
				title: "First Steps",
				content: readme_as_html
			});
			var overviewNode = document.getElementsByClassName("umcOverviewPane")[0];

			// app.js uses its subscription to /dojo/hashchange to show the right category
			// after a page reload. But this script is loaded after that event trigert.
			// So we have to manually check if we should show the first steps after
			// a page reload
			var hide_first_steps = window.location.hash !== "#category=_appliance_";
			domClass.toggle(detailsPane.domNode, 'dijitHidden', hide_first_steps);
			put(overviewNode, '-', detailsPane.domNode);
		}));
	};
	
	topic.subscribe('/dojo/hashchange', function(_hash) {
		// /dojo/hashchange publishes category and module changes
		var hash = decodeURIComponent(_hash);
		if (hash.length > 7 && hash.substr(0,8) === 'category') {
			var hide_first_steps = hash !== 'category=_appliance_';
			domClass.toggle(detailsPane.domNode, 'dijitHidden', hide_first_steps);
		}
	});

	load_first_steps();

	return null;
});
