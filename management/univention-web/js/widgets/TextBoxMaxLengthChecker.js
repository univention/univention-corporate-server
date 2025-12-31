/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/aspect",
	"dijit/Tooltip"
], function(declare, lang, array, on, aspect, Tooltip) {
	return declare(null, {
		// textBoxWidget: dijit.form.TextBox
		// 		The TextBox widget whose input is watched.
		// 		If the input is longer than maxLength a Tooltip
		// 		with a warning message is shown.
		// 		The content of the warning message is defined with the warningMessage attribute.
		textBoxWidget: null,

		// maxLength: Integer
		// 		The maximum amount of characters allowed in the textBoxWidget
		// 		before a warning message is shown.
		maxLength: null,

		// warningMessage: innerHTML String
		// 		The message that is shown in a tooltip.
		warningMessage: null,

		_listeners: null,
		_isTooltipActive: false,

		// constructor: function(textBoxWidget, maxLength, warningMessage) {
		constructor: function(args) {
			declare.safeMixin(this, args);

			this._listeners = [];
			this._listeners.push(on(this.textBoxWidget.textbox, 'input', lang.hitch(this, 'checkInput')));
			this._listeners.push(on(this.textBoxWidget.textbox, 'focus', lang.hitch(this, 'checkInput')));
			this._listeners.push(on(this.textBoxWidget.textbox, 'blur', lang.hitch(this, 'blur')));
			this._listeners.push(aspect.before(this.textBoxWidget, 'destroy', lang.hitch(this, 'dereference')));
		},

		usernameTooLong: function() {
			return this.textBoxWidget.get('value').length > this.maxLength;
		},

		checkInput: function() {
			if (this.usernameTooLong() && !this._isTooltipActive) {
				this._isTooltipActive = true;
				Tooltip.show(this.warningMessage, this.textBoxWidget.textbox);
			} else if (!this.usernameTooLong()) {
				this._isTooltipActive = false;
				Tooltip.hide(this.textBoxWidget.textbox);
			}
		},

		blur: function() {
			this._isTooltipActive = false;
			Tooltip.hide(this.textBoxWidget.textbox);
		},

		dereference: function() {
			array.forEach(this._listeners, function(iListener) {
				iListener.remove();
			});
			this.textBoxWidget = null;
		}
	});
});
