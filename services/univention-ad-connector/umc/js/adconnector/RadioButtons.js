/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/form/RadioButton",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane"
], function(declare, lang, array, RadioButton, tools, _FormWidgetMixin, ContainerWidget, LabelPane) {
	return declare("umc.modules.adconnector.RadioButtons", [ ContainerWidget, _FormWidgetMixin ], {
		value: null,

		staticValues: null,

		_radioButtons: null,

		name: null,

		// the class name of the widget as CSS class
		'class': 'umcRadioButtons',

		postMixInProperties: function() {
			this.inherited(arguments);
			if (!this.staticValues) {
				this.staticValues = [];
			}
			this.valid = false;
			this.sizeClass = null;
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._radioButtons = [];
			array.forEach(this.staticValues, function(ientry, i) {
				var radioButton = new RadioButton({
					name: this.name,
					value: ientry.id,
					labelPosition: 'right'
				});
				this._radioButtons[i] = radioButton;
				var labelPane = new LabelPane({
					content: radioButton,
					label: ientry.label
				});
				radioButton.watch('checked', lang.hitch(this, function(attr, oldval, newval) {
					var value = radioButton.get('value');
					if (newval) {
						this.set('value', value);
						this.set('valid', true);
					}
				}));
				this.addChild(labelPane);
			}, this);
		},

		_setValueAttr: function(value) {
			array.some(this.staticValues, function(ientry, i) {
				if (value == ientry.id) {
					this._radioButtons[i].set('checked', true);
					this._set('value', value);

					// break loop
					return true;
				}
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);
		}
	});
});

