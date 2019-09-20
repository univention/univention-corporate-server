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

/*global define,require,window*/

define([
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/json",
	"dojo/io-query",
	"dojo/cookie"
	//FIXME: for now, the text-loader cannot process .json files
	// -> http://bugs.dojotoolkit.org/ticket/15867
	// should be fixed later on
	//"dojo/text!/univention/languages.json"
], function(dojo, array, json, ioQuery, cookie) {
	/**
	 * @exports umc/i18n/tools
	 */
	var i18nTools = {};

	// i18nTools.availableLanguages: Object[]
	//		Dictonary with keys "id" and "label" of available languages They
	//		are configured by default in:
	//		/univention/language.json
	//		which is created by univention-config-registry using locale and
	//		umc/server/languages/*
	i18nTools.availableLanguages = [];
	try {
		// TODO
		i18nTools.availableLanguages = json.parse(require.getText('/univention/languages.json', false));
	}
	catch(e) { }

	// if we do not have any language available (we only localised
	// english and german, maybe the system has neither of them installed)
	// we "hack" availableLanguage because wherever we iterate over the
	// languages, we want to show at least one (and thus the possibility
	// to localise UMC). WARNING: This only works because we use English
	// strings when we translate. If English is not installed, we do not
	// translate anything, we just return the very same string.
	var en_us_present = false;
	array.forEach(i18nTools.availableLanguages, function(lang) {
		if (lang.id === 'en-US') {
			en_us_present = true;
		}
	});
	if (!en_us_present) {
		i18nTools.availableLanguages.push({id: 'en-US', label: 'English'});
	}

	i18nTools.setLanguage = function(/*String*/ locale) {
		// summary:
		//		Sets the new locale to locale by doing a redirect.
		// description:
		//		This function will set the frontend (dojo) and
		//		the backend (ucr) locale to locale. Due to
		//		dojo restrictions this can only be done by doing
		//		a redirect (losing all unsaved changes done in the
		//		current session!) with reasonable effort. This
		//		redirect is only done if necessary (i.e. if
		//		current locale != locale).
		// example:
		//		require(['i18nTools/i18nTools'], function(i18n) {
		//			i18n.setLanguage('de-DE'); // might do a redirect
		//			...
		//			i18n.setLanguage('de-DE'); // won't do it again
		//		});

		if (locale !== dojo.locale) {
			// reload the page when a different language is selected
			var query = ioQuery.queryToObject(window.location.search.substring(1));
			query.lang = locale;
			cookie('UMCLang', query.lang, { expires: 100, path: '/univention/' });
			if (window.location.pathname.indexOf('/univention/management/') === 0) {
				require('umc/tools').renewSession();
			}
			window.location.search = '?' + ioQuery.objectToQuery(query);
		}
	};

	/**
	 * @summary
	 *     Returns the default Language
	 *
	 * @description 
	 *     This function will retrieve the currently set Language (has to
	 *     be allowed, i.e. in i18nTools.availableLanguages) or a default
	 *     Language.  The currently set locale (dojo/_base/kernel.locale)
	 *     is set in the index.html either via the query string in the
	 *     URL, via a cookie, or via dojo automatically
	 *
	 * @returns {String} A languageTag specified by RFC 3066 (e.g. en-US)
	 */
	i18nTools.defaultLang = function () {
		var lowercase_locale = dojo.locale.toLowerCase();
		var exact_match = array.filter(i18nTools.availableLanguages, function(item) {
			return lowercase_locale === item.id.toLowerCase();
		});
		if (exact_match.length > 0) {
			return exact_match[0].id;
		}

		// fallbacks
		var default_language = null;

		// if dojo.locale is 'de' or 'de-XX' choose the first locale that starts with 'de'
		var short_locale = lowercase_locale.slice(0, 2);
		array.forEach(i18nTools.availableLanguages, function(lang) {
			if (lang.id.toLowerCase().indexOf(short_locale) === 0) {
				default_language = lang.id;
				return false;
			}
		}, this);

		if (null === default_language) {
			default_language = 'en-US';
		}

		return default_language;
	};

	return i18nTools;
});
