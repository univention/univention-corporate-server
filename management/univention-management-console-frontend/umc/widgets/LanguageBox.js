/*
 * Copyright 2012 Univention GmbH
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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.LanguageBox");

dojo.require("umc.i18n");
dojo.require("umc.widgets.ComboBox");

dojo.declare('umc.widgets.LanguageBox', [ umc.widgets.ComboBox, umc.i18n.Mixin ], {
	sizeClass: null,
	// use the framework wide translation file
	i18nClass: 'umc.app',

	availableLanguages: null,

	postMixInProperties: function() {
		this.availableLanguages = [
			{id: 'de-DE', label: this._('German')},
			{id: 'en-US', label: this._('English')}
		];
		this.staticValues = this.availableLanguages;
		this.value = this.defaultLang();
		// inherit at the end, because if no value is given
		// umc.widgets.ComboBox.postMixInProperties() sets value
		// to the first of staticValues eventually triggering
		// the onChange event
		this.inherited(arguments);
	},

	defaultLang: function () {
		// dojo.locale is set in the index.html either via the query string in the URL,
		// via a cookie, or via dojo automatically
		var lowercase_locale = dojo.locale.toLowerCase();
		var exact_match = dojo.filter(this.availableLanguages, function(item) {
			return lowercase_locale == item.id.toLowerCase();
		});
		if (exact_match.length > 0) {
			return exact_match[0].id;
		}

		// fallbacks
		var default_language = null;

		// if dojo.locale is 'de' or 'de-XX' choose the first locale that starts with 'de'
		var short_locale = lowercase_locale.slice(0, 2);
		dojo.forEach(this.availableLanguages, function(lang) {
			if (lang.id.toLowerCase().indexOf(short_locale) === 0) {
				default_language = lang.id;
				return false;
			}
		}, this);

		if (null === default_language) {
			default_language = 'en-US';
		}

		return default_language;
	},

	postCreate: function() {
		this.inherited(arguments);
		dojo.connect(this, 'onChange', function(lang) {
			if (lang != dojo.locale) {
				// reload the page when a different language is selected
				var query = dojo.queryToObject(window.location.search.substring(1));
				query.lang = lang;
				dojo.cookie('UMCLang', query.lang, { expires: 100, path: '/' });
				window.location.search = '?' + dojo.objectToQuery(query);
			}
		});
	}
});
