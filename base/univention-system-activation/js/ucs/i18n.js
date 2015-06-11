/*
 * Copyright 2011-2015 Univention GmbH
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
/*global define require console */

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/request",
	"dojo/json",
	"dojo/Deferred"
], function(lang, array, kernel, request, json, Deferred) {

	// return full path of a given scope
	var _scopePath = function(language, scope) {
		return lang.replace('{0}/{1}.json', [ scope, language ]);
	};

	// internal function and list of erroneous/missing translation information
	var _ignoreModules = {};
	var _ignore = function(language, scope) {
		scope = scope.replace(/\//g, '.');
		lang.setObject(lang.replace('{0}.{1}', [language, scope]), true, _ignoreModules);
	};
	var _ignored = function(language, scope) {
		scope = scope.replace(/\//g, '.');
		return lang.getObject(lang.replace('{0}.{1}', [language, scope]), false, _ignoreModules) || false;
	};

	// Internal regular expression to split locales in to the language and the
	// territory (which is ignored at the moment).
	var _i18nLocalRegExp = /^([a-z]{2,3})(_([a-z]{2,3}))?/i;

	// object which stores translation dict by path
	var cachedData = {};

	return {
		// summary:
		//		Plugin for internationalization, implements the _() function.
		// description:
		//		This plugin loads the json translation files given the current
		//		language settings and the specified scope. Its URI is deducted
		//		as follows. Given the module name "domain/mymodule", the mixin
		//		will try to load the JSON i18n file from
		//		"domain/i18n/<language>/mymodule.json".
		//		As parameter for the plugin, several scopes may be specified,
		//		e.g.  "umc/i18n!umc.branding,umc.app".
		//		The plugin provides a gettext-like method that will translate
		//		the given message string.  A printf-like syntax for the string
		//		is possible, simply provide the function with a dict or more
		//		arguments containing referenced variables.
		// example:
		//		Some examples of how the method can be used:
		// |	require(['umc/i18n!umc/branding,umc/app'], function(_) {
		// |		var msg = _('Translate me!');
		// |		msg = _('The total cost was %.2f EUR!', 10.2353);
		// |		msg = _('Hello %s %s!', 'John', 'Miller');
		// |		msg = _('Hello %(last)s, %(first)s!', { first: 'John', last: 'Miller' });
		// |	});

		load: function (params, req, load, config) {
			// detect the locale language (ignore territory)
			var m = _i18nLocalRegExp.exec(kernel.locale);
			var language = m[1] || 'en'; // default is English
			language = language.toLowerCase();

			// Internal dictionary of translation from English -> current language
			var _translations = [];

			var translate = function(/*String*/ _msg, /*mixed...*/ filler) {
				// get message to display (defaults to original message)
				var msg = _msg;
				var i = 0;
				for (i = 0; i < _translations.length; ++i) {
					if (_translations[i][_msg] && typeof _translations[i][_msg] == "string") {
						// we found a translation... take it and break the loop
						msg = _translations[i][_msg];
						break;
					}
				}

				// get arguments for lang.replace
				var args = [];
				if (arguments.length == 2 && typeof arguments[1] == 'object') {
					// we already have a dict as argument
					args = arguments[1];
				}
				else if (arguments.length > 1) {
					// we have a list of strings
					for (i = 1; i < arguments.length; ++i) {
						args.push(arguments[i]);
					}
				}

				// call lang.replace
				return lang.replace.apply(null, [msg, args]);
			};

			translate.inverse = function(/*String*/ _msg /*, String scope, ...*/) {
				// try to get the original message given the localized message
				// note: if the string has been expanded (e.g., with '%s' etc.)
				//       this will not be possible.
				var msg = null;
				var translations = _translations.slice(); // shallow copy
				var i;
				for (i = arguments.length - 1; i > 0; --i) {
					// add specified scopes
					var iscope = arguments[i];
					if (cachedData[iscope] !== undefined && !_ignored(language, iscope)) {
						// ok, we have this scope already loaded
						translations.unshift(cachedData[iscope]);
					}
				}

				// iterate over all scopes and try to find the original of the localized string
				for (i = 0; i < translations.length && msg === null; ++i) {
					// iterate over all entries of the scope
					for (var ikey in translations[i]) {
						if (translations[i].hasOwnProperty(ikey)) {
							var ival = translations[i][ikey];
							if (ival == _msg) {
								// we found the original
								msg = ikey;
								break;
							}
						}
					}
				}
				return msg || _msg; // return by default the localized string
			};

			var scopes = params.split(/\s*,\s*/);

			// somehow in the built dojo file, a dependency to "ucs/i18n!ucs"
			// is mapped to "ucs/i18n!ucs/main", fix this here
			scopes = array.map(scopes, function(iscope) {
				return iscope.replace(/\/main$/, '');
			});

			// ignore i18n files that could not be loaded previously
			scopes = array.filter(scopes, function(iscope) {
				return !_ignored(language, iscope);
			});

			// try to load the JSON translation file for the current language
			// via the dojo/text! plugin as dependencies
			var deferred = new Deferred();
			var ndone = 0;
			var results = [];
			var resolved = function() {
				// call the resolve function of the deferred if all requests are finished
				++ndone;
				if (ndone >= scopes.length) {
					deferred.resolve(results);
				}
			};

			array.forEach(scopes, function(iscope, i) {
				if (cachedData[iscope] !== undefined) {
					// we already have already cached the specified scope
					resolved();
					results[i] = cachedData[iscope];
					return;
				}

				// new scope, get the URL and load its JSON data
				var path = _scopePath(language, iscope);
				request(require.toUrl(path)).then(function(idata) {
					// parse JSON data and store results
					cachedData[iscope] = (results[i] = idata ? json.parse(idata) : null);
					resolved();
				}, function(error) {
					// i18n data could not be loaded, ignore them in the future
					_ignore(language, iscope);
					console.log(lang.replace('INFO: Localization files for scope "{0}" in language "{1}" not available!', [iscope, language]));

					resolved();
				});
			});

			// collect all results and call callback when everything is done
			deferred.then(function(results) {
				_translations = [];
				array.forEach(results, function(idata, i) {
					if (idata) {
						_translations.push(idata);
					}
				});

				// done -> return reference to translate function
				load(translate);
			});
		}
	};
});


