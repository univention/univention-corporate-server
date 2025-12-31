/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"umc/widgets/LabelPane",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/udm"
], function(declare, domClass, LabelPane, CheckBox, _) {
	return declare('umc.modules.udm.OverwriteLabel', [ LabelPane ], {
		// summary:
		//		Class that provides a widget in the form "[ ] overwrite" for multi-edit mode.

		postMixInProperties: function() {
			// force label and content
			this.content = new CheckBox({
				label: _('Overwrite'),
				value: false
			});

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'udmOverwriteLabel');
		},

		_setValueAttr: function(newVal) {
			this.content.set('value', newVal);
		},

		_getValueAttr: function() {
			return this.content.get('value');
		},

		addBetweenNonCheckBoxesClass: function() {
			return false;
		}
	});
});
