/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,require,console */

define([
	"./i18n/tools",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/request",
	"dojo/when",
	"dojo/promise/all",
	"dojo/json",
	"dojo/Deferred",
	"dojox/string/sprintf"
], function(i18nTools, lang, array, kernel, request, when, all, json, Deferred, sprintf) {

	// Internal helper function to split the module name into the module
	// path and name.
	var _i18nModNameRegExp = /^([^\/]*)$|^(.*)\/([^\/]*)$/;
	var _splitScope = function(scope) {
		// get module path and module name
		// case1: no '/' is in the path: m[2] == undefined && m[3] == undefined
		// case2: there is a '/' in the path: m[1] == undefined
		var m = _i18nModNameRegExp.exec(scope);
		var modPath = m[2] || '';
		var modName = m[3] || m[1];
		return [modPath, modName];
	};

	// return full path of a given scope
	var _scopePath = function(language, _scope) {
		var scope = _splitScope(_scope);
		return lang.replace('{1}/i18n/{0}/{2}.json', [ language, scope[0], scope[1] ]);
	};

	// Internal regular expression to split locales in to the language and the
	// territory (which is ignored at the moment).
	var _i18nLocalRegExp = /^([a-z]{2,3})(_([a-z]{2,3}))?/i;
	var _language = function() {
		// detect the locale language (ignore territory)
		var m = _i18nLocalRegExp.exec(kernel.locale);
		var language = m[1] || 'en'; // default is English
		return language.toLowerCase();
	};

	// object which stores translation dict by path
	var _cache = {};
	var _set = function(language, scope, translations) {
		lang.setObject(lang.replace('{0}.{1}', [language, scope]), translations, _cache);
	};
	var _load = function(language, scope) {
		// get the URL and load its JSON data
		var path = _scopePath(language, scope);
		var deferred = new Deferred();
		request(require.toUrl(path)).then(function(_data) {
			// parse JSON data and store results
			var data = _data ? json.parse(_data) : {};
			_set(language, scope, data);
			deferred.resolve(data);
		}, function(error) {
			// i18n data could not be loaded, ignore them in the future
			//_ignore(language, scope);
			console.log(lang.replace('INFO: Localization files for scope "{0}" in language "{1}" not available!', [scope, language]));
			_set(language, scope, {});
			deferred.resolve({});
		});
		_set(language, scope, deferred);
		return deferred;
	};
	var _get = function(language, scope) {
		var data = lang.getObject(lang.replace('{0}.{1}', [language, scope]), false, _cache);
		if (data !== undefined) {
			// we already have already cached the specified scope
			return data;
		}
		return _load(language, scope);
	};

	return {
		// summary:
		//		Plugin for internationalization, implements the _() and
		//		ngettext() functions.
		// description:
		//		This plugin loads the json translation files given the current
		//		language settings and the specified scope. Its URI is deducted
		//		as follows. Given the module name "domain/mymodule", the mixin
		//		will try to load the JSON i18n file from
		//		"domain/i18n/<language>/mymodule.json".
		//		As parameter for the plugin, several scopes may be specified,
		//		e.g.  "umc/i18n!umc/branding,umc/app".
		//		The plugin provides gettext-like methods that will translate
		//		the given message string. A printf-like syntax for the string
		//		is possible, simply provide the function with a dict or more
		//		arguments containing referenced variables.
		// example:
		//		Some examples of how the method can be used:
		// |	require(['umc/i18n!umc/branding,umc/app'], function(_) {
		// |		var msg = _('Translate me!');
		// |		msg = _('The total cost was %.2f EUR!', 10.2353);
		// |		msg = _('Hello %s!', 'John Miller');
		// |		msg = _('Hello %(last)s, %(first)s!', { first: 'John', last: 'Miller' });
		// |
		// |		msg = _.ngettext("There is one foo.", "There are %d foos.", n);
		// |		msg = _.ngettext("One file removed from directory %s",
		// |		                 "%d files removed from directory %s", n, dir);
		// |		msg = _.ngettext("In directory %2$s: removed one file.",
		// |		                 "In directory %2$s: removed %1$d files.", n, dir);
		// |	});

		load: function (params, req, load, config) {
			// Internal dictionary of translation from English -> current language
			//var _translations = [];

			// use 'umc.app' and 'umc.branding' as backup path to allow other class to override a
			// UMC base class without losing its translations (see Bug #24864)
			var scopes = params.split(/\s*,\s*/);
			scopes.push('umc/branding');
			scopes.push('umc/app');

			// filter out empty scopes
			scopes = array.filter(scopes, function(iscope) {
				return iscope;
			});

			var translate = function(/*String*/ msg, /*mixed...*/ filler) {
				// get message to display (defaults to original message)
				var language = _language();
				var _msg = '';
				var _data = {};
				var i = 0;
				for (i = 0; i < scopes.length; ++i) {
					_data = _get(language, scopes[i]);
					_msg = _data[msg];
					if (_msg && typeof _msg === "string") {
						// we found a translation... break the loop
						msg = _msg;
						break;
					}
				}

				// get arguments for sprintf
				var args = [msg];
				for (i = 1; i < arguments.length; ++i) {
					args.push(arguments[i]);
				}

				// call sprintf
				var result = msg;
				try {
					result = sprintf.apply(null, args);
				} catch(err) {
					console.warn(err);
				}
				return result;
			};

			// Arguments: translate.ngettext(String, String, number, mixed)
			translate.ngettext = function( id, id_plural, n, filler) {
				var language = _language();
				var _msg = '';
				var msg = '';
				var plural;
				var _data = {};
				var i = 0;
				
				for (i = 0; i < scopes.length; ++i) {
					_data = _get(language, scopes[i]);
					_msg = _data[id];
					if (_msg instanceof Array && _msg.length > 0) {
						// we found the array with translations for all the
						// plural forms. Pick the right one and break the loop.
						try {
							plural = Function('n', '"use strict";return ' + _data.$plural$ + ';')(n);
						} catch (exc) {
							plural = 1;
						}
						// Catch the special case, where the expression in
						// _data.$plural$ is "n>1" (or similar) and returns a bool.
						if (typeof plural === "boolean") {
							plural = plural ? 1 : 0;
						}
						
						msg = _msg[plural];
						break;
					}
				}

				// When no translation was found just build the english plural.
				if (!msg) {
					if (n === 1) {
						msg = id;
					} else {
						msg = id_plural;
					}
				}

				// Check if the "%d" for n was omitted in the translation
				// and don't include n in the arguments list if so.
				//
				// But only when not using argument swapping!!!
				// When "%1$d" exists in id_plural just proceed normal.
				// sprintf will just skip the first argument (since all
				// other "%xx" will be hard-linked to a certain argument,
				// too, in this case).
				var vars_in_msg = msg.match(/(^|[^%])%[^%]/g);
				var var_cnt_in_msg = vars_in_msg ? vars_in_msg.length : 0;
				var args = [msg];
				if (id_plural.search(/(^|[^%])\%1\$/) === -1 && arguments.length-2 > var_cnt_in_msg) {
					// get arguments for sprintf (leaving out n)
					for (i = 3; i < arguments.length; ++i) {
						args.push(arguments[i]);
					}
				}
				else {
					// get arguments for sprintf
					for (i = 2; i < arguments.length; ++i) {
						args.push(arguments[i]);
					}
				}

				// call sprintf
				return sprintf.apply(null, args);
			};

			translate.inverse = function(/*String*/ _msg /*, String scope, ...*/) {
				// try to get the original message given the localized message
				// note: if the string has been expanded (e.g., with '%s' etc.)
				//       this will not be possible.

				// iterate over all scopes and try to find the original of the localized string
				var language = _language();
				var msg = null;
				var _data = {};
				var i, ival, ikey;
				for (i = 0; i < scopes.length && msg === null; ++i) {
					_data = _get(language, scopes[i]);

					// iterate over all entries of the scope
					for (ikey in _data) {
						if (_data.hasOwnProperty(ikey)) {
							ival = _data[ikey];
							if (ival === _msg) {
								// we found the original
								msg = ikey;
								break;
							}
						}
					}
				}
				return msg || _msg; // return by default the localized string
			};

			translate.load = function() {
				// try to load the JSON translation files for the current language
				var language = _language();
				var deferreds = array.map(scopes, function(iscope) {
					return _get(language, iscope);
				});
				return all(deferreds);
			};

			translate.scopes = scopes;

			translate.load().then(function() {
				load(translate);
			});
		}
	};
});


