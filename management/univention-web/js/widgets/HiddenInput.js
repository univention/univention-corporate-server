/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dijit/form/TextBox",
	"umc/widgets/_FormWidgetMixin"
], function(declare, TextBox, _FormWidgetMixin) {
	return declare("umc.widgets.HiddenInput", [ TextBox, _FormWidgetMixin ], {
		type: 'hidden',

		// the widget's class name as CSS class
		baseClass: 'umcHiddenInput',

		// do not display labels via the LabelPane
		displayLabel: false

	});
});

