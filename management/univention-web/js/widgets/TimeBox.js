/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dijit/form/TimeTextBox",
	"dojox/string/sprintf",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools"
], function(declare, lang, TimeTextBox, sprintf, ContainerWidget, _FormWidgetMixin, tools) {
	return declare("umc.widgets.TimeBox", [ ContainerWidget, _FormWidgetMixin ], {
		// the widget's class name as CSS class
		baseClass: 'umcTimeBox',

		_timeBox: null,

		disabled: false,

		buildRendering: function() {
			this.inherited(arguments);

			this._timeBox = new TimeTextBox({
				name: this.name,
				disabled: this.disabled
			});
			this.addChild(this._timeBox);

			// hook to value changes
			this.own(this._timeBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', this.get('value'));
			})));
		},

		_dateToTime: function(dateObj) {
			if (dateObj === null) {
				return '';
			}
			try {
				return sprintf('%02d:%02d', dateObj.getHours(), dateObj.getMinutes());
			} catch(e) {
				return '';
			}
		},

		// return time in the format 'HH:MM'
		_getValueAttr: function() {
			return this._dateToTime(this._timeBox.get('value'));
		},

		_setValueAttr: function(newVal) {
			if (newVal === '') { newVal = null; } // set empty input instead of default value 00:00
			if (newVal && newVal instanceof Date) {
				newVal = this._dateToTime(newVal);
			}
			try {
				var parts = newVal.split(':');
				this._timeBox.set('value', new Date(1970, 1, 1, parseInt(parts[0], 10) || 0, parseInt(parts[1], 10) || 0));
			} catch(e) {
				console.log('ERROR: invalid time format: ' + newVal);
				this._timeBox.set('value', null);
			}
		},

		isValid: function() {
			// use the property 'valid' in case it has been set
			// otherwise fall back to the default
			if (null !== this.valid) {
				return this.get('valid');
			}
			return this._timeBox.isValid();
		},

		_setBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			tools.delegateCall(this, arguments, this._timeBox);
		},

		_getBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			tools.delegateCall(this, arguments, this._timeBox);
		}
	});
});


