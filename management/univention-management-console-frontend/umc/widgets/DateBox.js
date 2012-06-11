/*
 * Copyright 2011-2012 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.DateBox");

dojo.require("dijit.form.DateTextBox");
dojo.require("dojox.string.sprintf");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.DateBox", [
	umc.widgets.ContainerWidget,
	umc.widgets._FormWidgetMixin,
	umc.widgets._WidgetsInWidgetsMixin
], {
	// the widget's class name as CSS class
	'class': 'umcDateBox',

	_dateBox: null,

	sizeClass: null,

	disabled: false,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;
	},

	buildRendering: function() {
		this.inherited(arguments);

		this._dateBox = this.adopt(dijit.form.DateTextBox, {
			name: this.name,
			disabled: this.disabled
		});
		this.addChild(this._dateBox);

		// hook to the onChange event
		this.connect(this._dateBox, 'onChange', 'onChange');
	},

	_dateToString: function(dateObj) {
		return dojox.string.sprintf('%04d-%02d-%02d', dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate());
	},

	// return ISO8601/RFC3339 format (yyyy-MM-dd) as string
	_getValueAttr: function() {
		var dateObj = this._dateBox.get('value');
		if (dateObj && dateObj instanceof Date) {
			return this._dateToString(dateObj);
		}
		return dateObj;
	},

	_setValueAttr: function(/*String|Date*/ newVal) {
		if (newVal && newVal instanceof Date) {
			newVal = this._dateToString(newVal);
		}
		this._dateBox.set('value', newVal);
	},

	isValid: function() {
		// use the property 'valid' in case it has been set
		// otherwise fall back to the default
		if (null !== this.valid) {
			return this.get('valid');
		}
		return this._dateBox.isValid();
	},

	_setBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		umc.tools.delegateCall(this, arguments, this._dateBox);
	},

	_getBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		umc.tools.delegateCall(this, arguments, this._dateBox);
	}
});



