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
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/request/xhr",
	"dojo/io-query",
	"dojo/json"
], function(lang, xhr, ioQuery, json) {
	return {
		load: function(id, require, load, headers) {
			// id: String
			//		Path to the resource
			// require: Function
			//		Object that include the function toUrl with given id returns a valid URL from which to load the text.
			// load: Function
			//		Callback function which will be called, when the loading finished.

			// id is something like (path is always absolute):
			//   "path/to/data.json"
			//   "path/to/data.json!timeout=500&"
			// The parameters after "!" are passed over to xhr.get().

			var parts = id.split("!");
			var url = require.toUrl(parts[0]);

			var _getCustomParams = function() {
				var hasFlags = parts.length > 1;
				if (hasFlags) {
					return ioQuery.queryToObject(parts[1]);
				}
				return {};
			};

			var params = lang.mixin({
				handleAs: 'json',
				timeout: 10000,
				headers: headers
			}, _getCustomParams());

			xhr.get(url, params).then(function(data) {
				load(data);
			}, function(err) {
				console.error(lang.replace('Could not load JSON data from {0}: {1}', [ id, err ]));
				load({});
			});
		}
	};
});

