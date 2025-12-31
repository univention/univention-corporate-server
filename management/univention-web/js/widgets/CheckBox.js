/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dijit/form/CheckBox",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin",
	"./Icon"
], function(declare, lang, domClass, domConstruct, CheckBox, tools, _FormWidgetMixin, Icon) {
	return declare("umc.widgets.CheckBox", [ CheckBox, _FormWidgetMixin ], {
		// by default, the checkbox is turned off
		value: false,

		// a checkbox is always true
		valid: true,

		// display the label on the right
		labelPosition: 'right',

		// internal cache of the initial value
		_initialValue: null,

		postMixInProperties: function() {
			this._initialValue = this.checked = this.value;
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var iconCheck = new Icon({
				iconName: 'check'
			});
			var iconIndeterminate = new Icon({
				iconName: 'minus'
			});
			this.own(iconCheck);
			this.own(iconIndeterminate);
			domConstruct.place(iconCheck.domNode, this.domNode, 'first');
			domConstruct.place(iconIndeterminate.domNode, this.domNode, 'first');

			var node = domConstruct.create('div', {
				'class': 'dijitCheckBoxInputStretcher'
			}, this.focusNode, 'after');
			domConstruct.place(this.focusNode, node);
		},

		postCreate: function() {
			this.inherited(arguments);
			this.own(
				this.watch("checked", lang.hitch(this, function(attr, oldVal, newVal) {
					this.set('indeterminate', false);
					this.set("value", newVal);
				}))
			);
		},

		_setValueAttr: function(/*String|Boolean*/ newValue, /*Boolean*/ priorityChange){
			// based on the code from dijit.form.CheckBox
			newValue = tools.isTrue( newValue );

			// this is important, otherwise the initial state is displayed wrong
			if(this._created){
				this.set('checked', newValue, priorityChange);
			}
			this._set("value", newValue);
		},

		indeterminate: false,
		_setIndeterminateAttr: function(indeterminate) {
			this.focusNode.indeterminate = indeterminate;
			var ariaValue = indeterminate ? 'mixed' : this.get('checked').toString();
			this.focusNode.setAttribute('aria-checked', ariaValue);
			domClass.toggle(this.domNode, 'dijitCheckBoxIndeterminate', indeterminate);
			this._set('indeterminate', indeterminate);
		},

		_getValueAttr: function() {
			return this.get('checked');
		},

		setValid: function(isValid, message) {
			// a checkbox cannot be invalid
			// (for now, we should consider implementing it!)
			return false;
		}
	});
});


