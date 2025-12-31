/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

