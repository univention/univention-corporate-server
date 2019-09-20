/*
 * Copyright 2017-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
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

		usernameTooLong: function() {  // do not rename without considering uvmm!
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
