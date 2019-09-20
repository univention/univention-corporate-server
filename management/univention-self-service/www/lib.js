/*
 * Copyright 2015-2019 Univention GmbH
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
/*global define */

define([
	"dojo/_base/lang",
	"dojo/hash",
	"dojo/io-query",
	"dojox/html/entities",
	"umc/i18n!."
], function(lang, hash, ioQuery, htmlEntities, _) {

	return {
		getCurrentLanguageQuery: function() {
			return '?lang=' + (this.getQuery('lang') || 'en-US');
		},

		/**
		 * Returns relative url from query string.
		 */
		_getUrlForRedirect: function() {
			var queryUrl = this.getQuery('url');
			if (queryUrl) {
				if (this._isUrlRelative(queryUrl)) {
					return queryUrl;
				} else {
					var msg = {
						content: lang.replace(_('Forbidden redirect to: {0}\n The url has to start with (only) one "/".', [queryUrl])),
						'class': 'error'
					};
					this.showMessage(msg);
				}
			}
			return "/univention/";
		},

		/** Returns boolean if given url is relative.
		 * @param {string} url - url to test
		 * */
		_isUrlRelative: function(url) {
				var reg = /^\/([^\/]|$)/;
				var isUrlRelative = reg.test(url);
				return isUrlRelative;
		},

		/**
		 * Returns the value of the query string for a given key.
		 * */
		getQuery: function(key) {
			var queryObject = ioQuery.queryToObject(window.location.search.slice(1));
			lang.mixin(queryObject, ioQuery.queryToObject(hash()));
			return queryObject[key];
		}
	};
});
