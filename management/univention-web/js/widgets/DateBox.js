/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
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
	"dojo/query",
	"dojo/aspect",
	"dojox/string/sprintf",
	"dijit/form/DateTextBox",
	"umc/widgets/Calendar",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/Button",
	"umc/widgets/Icon",
	"umc/tools",
	"put-selector/put"
], function(declare, lang, query, aspect, sprintf, DateTextBox, Calendar, ContainerWidget, _FormWidgetMixin, Button,
		Icon, tools, put) {

	var _DateTextBox = declare([DateTextBox, _FormWidgetMixin], {
		buildRendering: function() {
			this.inherited(arguments);

			// exchange validation icon node
			var icon = new Icon({
				'class': 'umcTextBox__validationIcon',
				iconName: 'alert-circle'
			});
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', icon.domNode);
			put(validationContainerNode, '!');

			// exchange dropdown icon node
			var button = new Button({
				iconClass: 'chevron-down',
				'class': 'ucsIconButton umcTextBox__downArrowButton',
				tabIndex: '-1'
			});
			put(this._buttonNode, '+', button.domNode);
			put(this._buttonNode, '!');
			this._buttonNode = button.domNode;
		}
	});

	return declare("umc.widgets.DateBox", [ ContainerWidget, _FormWidgetMixin ], {
		_dateBox: null,

		disabled: false,

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._dateBox = this.own(new _DateTextBox({
				popupClass: Calendar,
				name: this.name,
				disabled: this.disabled
			}))[0];
			this.addChild(this._dateBox);

			// hook to the onChange event
			this.own(this._dateBox.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', this._dateToString(newVal));
			})));
		},

		_dateToString: function(dateObj) {
			/* convert input to ISO8601
			 * input: string or Date object
			 * output: string in ISO format if dateObj is valid; null otherwise
			 */
			if (dateObj instanceof Date) {
				return sprintf('%04d-%02d-%02d', dateObj.getFullYear(), dateObj.getMonth() + 1, dateObj.getDate());
			}
			// special case: transform german 31.01.2020 into 2020-01-31
			if (typeof dateObj == 'string' && dateObj.match(date_de_format)) {
				var date = dateObj.split('.');
				var year = date[2];
				var month = date[1];
				var day = date[0];
				// very special case: support the backend syntax "date", which has no century. guess it.
				if (year.length === 2){
					if (Number(year) > 60) {
						year = sprintf('19%d', year);
					} else {
						year = sprintf('20%02d', year);
					}
				}
				return sprintf('%04d-%02d-%02d', year, month, day);
			}
			// either already in ISO8601 format, or an empty string which must be transformed to null!
			return dateObj || null;
		},

		// return ISO8601/RFC3339 format (yyyy-MM-dd) as string or null if no date is set
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

		state: '',
		setValid: function(isValid, message) {
			this.inherited(arguments); // for the 'state' handling
			return this._dateBox.setValid(isValid, message);
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


