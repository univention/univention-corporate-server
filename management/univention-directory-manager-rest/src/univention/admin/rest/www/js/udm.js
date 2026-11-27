/*
 * SPDX-FileCopyrightText: 2019-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
