/*
 * Copyright 2017-2019 Univention GmbH
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
/* global require */
function getQuery(/*String*/ param, /*mixed*/ defaultVal) {
	// parse the URI query string
	var query = window.location.search.substring(1);
	var vars = query.split('&');
	for (var i = 0; i < vars.length; i++) {
		// parse the tuple
		var tuple = vars[i].split('=');

		// check whether we found the particular parameter we are interested in
		if (2 === tuple.length && param === decodeURIComponent(tuple[0])) {
			return decodeURIComponent(tuple[1]);
		}
	}

	// otherwise return the specified default value
	return defaultVal;
}

function getCookie(/*String*/ param, /*mixed*/ defaultVal) {
	// find the given parameter in the cookie string
	var reg = new RegExp(param + '=([a-zA-Z_-]*)');
	var m = reg.exec(document.cookie);
	if (m && m[1]) {
		return m[1];
	}

	// in case the parameter does not exist, return the default value
	return defaultVal;
}

function getLocale() {
	var locale = getQuery('lang') || getCookie('UMCLang');
	if (locale) {
		locale = locale.replace('_', '-');
	}
	return locale;
}

function _getPackageName() {
	// return the name of the AMD package based on the current URI
	var parts = location.pathname.split('/');
	for (var i = parts.length - 1; i >= 0; --i) {
		if (parts[i]) {
			return parts[i];
		}
	}
	return 'unknown';
}

function mixin(a, b) {
	// mixin in all values from b into a
	for (var ikey in b) {
		if (b.hasOwnProperty(ikey)) {
			a[ikey] = b[ikey];
		}
	}
	return a;
}

// umcConfig can be extended in the index.html of each webapp
// make sure to mixin default values into an already existing umcConfig
if (typeof umcConfig === 'undefined') {
	var _customUmcConfig = {};
	var umcConfig = {};
} else {
	// save the user defined umcConfig
	var _customUmcConfig = umcConfig;
}
umcConfig = mixin({
	allowLanguageSwitch: true,
	forceLogin: false,
	autoLogin: true,
	loadHooks: true,
	deps: [],
	callback: function() {}
}, _customUmcConfig);

// prepare all needed dependencies and evaluate umcConfig settings
var _deps = ["dojo/parser", "login", "umc/tools", "umc/json!/univention/get/meta", "umc/menu/Button", "umc/widgets/LoginButton"];
_deps.push("dojo/domReady!");
var _ndeps = _deps.length; // save current number of dependencies

// add the specified dependencies from umcConfig
_deps = _deps.concat(umcConfig.deps);

// define dojoConfig and make sure to mix user defined values into dojoConfig
if (typeof dojoConfig === 'undefined') {
	var _customDojoConfig = {};
	var dojoConfig = {};
} else {
	// save the user defined dojoConfig
	var _customDojoConfig = dojoConfig;
}
dojoConfig = mixin({
	has: {
		'dojo-undef-api': true
	},
	isDebug: getQuery('debug') === '1',
	locale: getLocale(),
	async: true,
	packages: [{
		name: _getPackageName(),
		location: location.pathname.substring(0, location.pathname.length - 1)
	}, {
		name: 'login',
		location: '/univention/login'
	}],
	map: {},
	deps: _deps,
	callback: function(parser, login, tools, meta) {
		mixin(tools._status, meta.result);
		if (umcConfig.loadHooks) {
			require(["umc/hooks!", "umc/piwik"]);
		}
		var customDeps = Array.prototype.slice.call(arguments, _ndeps);
		parser.parse();
		if (umcConfig.autoLogin) {
			login.start(undefined, undefined, !umcConfig.forceLogin);
		}
		umcConfig.callback.apply(umcConfig, customDeps);
	}
}, _customDojoConfig);
