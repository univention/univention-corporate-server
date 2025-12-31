/*
 * SPDX-FileCopyrightText: 2025-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/widgets/DateBox",
	"umc/widgets/TimeBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools",
], function(declare, lang, DateBox, TimeBox, ContainerWidget, _FormWidgetMixin, tools) {

	return declare("umc.widgets.DateBox", [ ContainerWidget, _FormWidgetMixin ], {
		_dateBox: null,
		_timeBox: null,

		disabled: false,

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._dateBox = this.own(new DateBox({
				name: this.name + '-date',
				disabled: this.disabled
			}))[0];
			this.addChild(this._dateBox);

			this._timeBox = this.own(new TimeBox({
				name: this.name + '-time',
				disabled: this.disabled
			}))[0];
			this.addChild(this._timeBox);

			// hook to the onChange event
			this.own(this._dateBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', newVal + 'T' + this._timeBox.get('value') + ':00');
			})));
			this.own(this._timeBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', this._dateBox.get('value') + 'T' + newVal + ':00');
			})));
		},

		// return ISO8601/RFC3339 format (YYYY-MM-DDTHH:MM:SS) as string or null if no date is set
		_getValueAttr: function() {
			return this._dateBox.get('value') + 'T' + this._timeBox.get('value');
		},

		_setValueAttr: function(/*String|Date*/ newVal) {
			if (typeof newVal === 'string') {
				const [date, time] = newVal.split("T");
			} else {
				const date = newVal;
				const time = newVal;
			}
			this._dateBox.set('value', date);
			this._timeBox.set('value', time);
			this._set('value', newVal);
		},

		isValid: function() {
			// use the property 'valid' in case it has been set
			// otherwise fall back to the default
			if (null !== this.valid) {
				return this.get('valid');
			}
			return this._dateBox.isValid() && this._timeBox.isValid();
		},

		state: '',
		setValid: function(isValid, message) {
			this.inherited(arguments); // for the 'state' handling
			return this._dateBox.setValid(isValid, message);
			return this._timeBox.setValid(isValid, message);
		},

		_setBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			tools.delegateCall(this, arguments, this._dateBox);
			tools.delegateCall(this, arguments, this._timeBox);
		},

		_getBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			tools.delegateCall(this, arguments, this._dateBox);
			tools.delegateCall(this, arguments, this._timeBox);
		}
	});
});
