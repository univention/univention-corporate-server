/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, _WidgetBase, _TemplatedMixin) {
	return declare("StandbyCircle", [_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			// we have to wrap the svg in a div because svg elements behave differently in regards to setting style
			// and classes (which is needed for Standby.js)
			'<div class="umcStandbySvgWrapper">' +
				'<svg class="umcStandbySvg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
					'<circle class="umcStandbySvg__circle" cx="50" cy="50" r="45"></circle>' +
				'</svg>' +
			'</div>'
	});
});
