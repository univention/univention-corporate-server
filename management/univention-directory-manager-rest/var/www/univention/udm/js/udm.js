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
/*global console*/

dojoConfig.packages.push({
	name: 'management',
	location: '/univention/management'
});
dojoConfig.map = {
	'*': {
		'umc/modules': 'management/modules'
	}
};

var umcConfig = {
	allowLanguageSwitch: false,
	forceLogin: false,
	autoLogin: false,
	loadHooks: false,
	callback: function() {
		require(['dojo/query'], function(query) {
			var schema = query('link[rel=describedby]');
			//if (schema && schema[0]) {
			//	getHelp(schema[0].href, 'OPTIONS');
			//}

		});
	}
};
function help() {
	require(['dojo/query'], function(query) {
		var schema = query('link[rel=describedby]');
		if (schema && schema[0]) {
			getHelp(schema[0].href, 'OPTIONS');
		}

	});
};

function getHelp(url, method) {
	require(['dojo/_base/lang', 'dojo/dom', 'dojo/query', 'dojo/dom-construct', 'dojo/request/xhr', 'dojox/xml/parser'], function(lang, dom, query, domConst, xhr, parser) {
		return xhr(url, {
				method: method || 'GET',
				preventCache: false,
				//handleAs: 'json',
				handleAs: 'xml',
				headers: lang.mixin({
				//		'Accept-Language': require('umc/i18n/tools').defaultLang(),
				//		'Accept': 'application/json; q=1.0, text/html; q=0.3; */*; q=0.1',
				//		'X-XSRF-Protection': tools.getCookies().sessionID,
				//		'Content-Type': 'application/json'
				}),
				withCredentials: true
		}).then(function(xmldoc) {
//			console.log(query('nav', parser.parse(xmldoc)));
//			umc.dialog.alert(domConst.toDom(xmldoc));
			domConst.place(xmldoc, query('body')[0], 'replace')
		});
	});

}
