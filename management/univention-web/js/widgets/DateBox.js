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
/*global define */

var date_de_format = /^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+$/;

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"dojox/string/sprintf",
	"dijit/form/DateTextBox",
	"umc/widgets/Calendar",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools"
], function(declare, lang, aspect, sprintf, DateTextBox, Calendar, ContainerWidget, _FormWidgetMixin, tools) {
	return declare("umc.widgets.DateBox", [ ContainerWidget, _FormWidgetMixin ], {
		_dateBox: null,

		disabled: false,

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._dateBox = this.own(new DateTextBox({
				popupClass: Calendar,
				name: this.name,
				disabled: this.disabled
			}))[0];
			this.addChild(this._dateBox);

			// hook to the onChange event
			this.own(this._dateBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', this._dateToString(newVal));
			})));

			this.own(aspect.after(this._dateBox, 'closeDropDown', lang.hitch(this, function() {
				this._dateBox.dropDown.hideTooltip();
			})));
		},

		_dateToString: function(dateObj) {
			// convert input to ISO8601
			// input: string or Date object
			// output: string in ISO format
			if (dateObj) {
				if (dateObj instanceof Date) {
					return sprintf('%04d-%02d-%02d', dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate());
				} else if (typeof dateObj == 'string' && dateObj.match(date_de_format)) {
					var date = dateObj.split('.');
					var year = date[2];
					var month = date[1];
					var day = date[0];
					if (year.length <= 4){
						// guessing the century; pretty stupid
						if (Number(year) > 60) {
							year = sprintf('19%d', year);
						} else {
							year = sprintf('20%02d', year);
						}
					}
					return sprintf('%04d-%02d-%02d', year, month, day);
				}
			}
			return dateObj;
		},

		// return ISO8601/RFC3339 format (yyyy-MM-dd) as string
		_getValueAttr: function() {
			return this._dateToString(this._dateBox.get('value'));
		},

		_setValueAttr: function(/*String|Date*/ newVal) {
			newVal = this._dateToString(newVal);
			this._dateBox.set('value', newVal);
			this._set('value', newVal);
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
			tools.delegateCall(this, arguments, this._dateBox);
		},

		_getBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			tools.delegateCall(this, arguments, this._dateBox);
		}
	});
});


