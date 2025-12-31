/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/tools",
	"umc/widgets/Form",
], function(declare, lang, tools, Form) {
	return declare("umc.modules.appcenter.AppSettingsForm", [ Form ], {
		_getValueAttr: function() {
			return tools.objFilter(this.inherited(arguments), lang.hitch(this, function(k, _) {
				return !this.getWidget(k).get('disabled');
			}));
		},
	});
});

