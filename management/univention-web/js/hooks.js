/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Evented",
	"umc/json!/univention/js/umc/hooks.json"
], function(declare, lang, array, Evented, hookData) {
	var deps = array.map(hookData, function(idata) {
		return 'umc/hooks/' + idata.path;
	});

	return {
		load: function(params, req, load) {
			require(deps, function() {
				load(null);
			});
		}
	};
});
