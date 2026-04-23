/*
 * SPDX-FileCopyrightText: 2025-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	// "dojo/promise/all",
	"umc/widgets/DateBox",
	"umc/widgets/TimeBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/render",
	"umc/tools",
], function(declare, lang, /*all,*/ DateBox, TimeBox, ContainerWidget, _FormWidgetMixin, render, tools) {

	return declare("umc.widgets.DateTimeBox", [ ContainerWidget, _FormWidgetMixin ], {
		_dateBox: null,
		_timeBox: null,

		disabled: false,

		buildRendering: function() {
			this.inherited(arguments);

			// render the widgets and layout them
			this._widgets = render.widgets([{
				type: DateBox,
				name: this.name + '-date',
				disabled: this.disabled,
				required: this.required
			}, {
				type: TimeBox,
				name: this.name + '-time',
				disabled: this.disabled,
				required: this.required
			}], this);

			this._dateBox = this._widgets[this.name + '-date'];
			this._timeBox = this._widgets[this.name + '-time'];
			this._container = render.layout([[this.name + '-date', this.name + '-time']], this._widgets);

			// register for value changes
			this.own(this._dateBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', newVal + 'T' + this._timeBox.get('value') + ':00');
			})));
			this.own(this._timeBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', this._dateBox.get('value') + 'T' + newVal + ':00');
			})));

			this.addChild(this._container);
		},

		// ready: function() {
		// 	return all([this._dateBox.ready(), this._timeBox.ready(), this.inherited(arguments)]);
		// },

		// return ISO8601/RFC3339 format (YYYY-MM-DDTHH:MM:SS) as string or null if no date is set
		_getValueAttr: function() {
			var date = this._dateBox.get('value');
			var time = this._timeBox.get('value');

			if (!date || !time) {
				return null;
			}
			return date + 'T' + time + ':00';
		},

		_setValueAttr: function(/*String|Date*/ newVal) {
			var date, time;
			if (typeof newVal === 'string') {
				var sep = newVal.includes('T') ? 'T' : ' ';
				[date, time] = newVal.split(sep);
			} else {
				date = newVal;
				time = newVal;
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
