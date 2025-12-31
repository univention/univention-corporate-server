/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dijit/form/RadioButton",
	"dijit/registry",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin"
], function(declare, array, RadioButton, registry, tools, _FormWidgetMixin) {
	return declare("umc.widgets.RadioButton", [ RadioButton, _FormWidgetMixin ], {
		value: null,

		// name: String
		//		Should be different for each radio button, so that it can be layout
		//		idependently.
		name: null,

		// radioButtonGroup: String
		//		Specifies the group of radio buttons that shares one value.
		radioButtonGroup: null,

		// display the label on the right
		labelPosition: 'right',

		postMixInProperties: function() {
			if (!this.value) {
				this.value = this.name;
			}
			this.name = this.radioButtonGroup;
			this.inherited(arguments);
			this.valid = false;
			this.sizeClass = null;
		},

		_getRelateWidgets: function() {
			// summary:
			//		Return all widgets of the same radio button group.
			var form = registry.getEnclosingWidget(this.focusNode.form);
			var relatedWidgets = [];
			tools.forIn(form._widgets, function(key, widget) {
				if (widget.radioButtonGroup == this.radioButtonGroup) {
					relatedWidgets.push(widget);
				}
			}, this);
			return relatedWidgets;
		},

		_getValueAttr: function() {
			return Boolean(this.inherited(arguments));
		},

		_getValidAttr: function() {
			var checkButtons = array.filter(this._getRelateWidgets(), function(iwidget) {
				return iwidget.get('checked');
			});
			return checkButtons.length == 1;
		},

		setValid: function(isValid, message) {
			// a checkbox cannot be invalid
			// (for now, we should consider implementing it!)
			return false;
		}
	});
});

