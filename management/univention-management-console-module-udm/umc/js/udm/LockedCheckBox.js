/*
 * SPDX-FileCopyrightText: 2018-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojo/on",
	"dojo/keys",
	"dojo/dom-construct",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/CheckBox",
], function(declare, lang, array, when, on, keys, domConstruct, Deferred, tools, CheckBox) {
	return declare("umc.modules.udm.LockedCheckBox", [ CheckBox ], {
		// summary:
		//		This class extends the normal CheckBox in order to encapsulate
		//		some UDM specific behavior.

		setInitialValue: function(value) {
			this.set('value', value);
			if (value === '0') {
				this.set('disabled', true);
			}
		}

	});
});

