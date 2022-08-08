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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/query",
	"dijit/form/TimeTextBox",
	"dojox/string/sprintf",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/Button",
	"umc/widgets/Icon",
	"umc/tools",
	"put-selector/put"
], function(declare, lang, query, TimeTextBox, sprintf, ContainerWidget, _FormWidgetMixin, Button, Icon, tools, put) {

	var _TimeTextBox = declare([TimeTextBox, _FormWidgetMixin], {
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

	return declare("umc.widgets.TimeBox", [ ContainerWidget, _FormWidgetMixin ], {
		// the widget's class name as CSS class
		baseClass: 'umcTimeBox',

		_timeBox: null,

		disabled: false,

		buildRendering: function() {
			this.inherited(arguments);

			this._timeBox = new _TimeTextBox({
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
			if (dateObj instanceof Date) {
				return sprintf('%02d:%02d', dateObj.getHours(), dateObj.getMinutes());
			}
			return dateObj || null;
		},

		// return time in the format 'HH:MM'
		_getValueAttr: function() {
			return this._dateToTime(this._timeBox.get('value'));
		},

		_setValueAttr: function(newVal) {
			if (newVal instanceof Date) {
				newVal = this._dateToTime(newVal);
			}
			if (newVal && typeof newVal === 'string') {
				var parts = newVal.split(':');
				try {
					newVal = new Date(1970, 1, 1, parseInt(parts[0], 10) || 0, parseInt(parts[1], 10) || 0);
				} catch(e) {
					console.error('invalid time format: ' + newVal);
				}
			}
			this._timeBox.set('value', newVal || null);
		},

		isValid: function() {
			// use the property 'valid' in case it has been set
			// otherwise fall back to the default
			if (null !== this.valid) {
				return this.get('valid');
			}
			return this._timeBox.isValid();
		},

		state: '',
		setValid: function(isValid, message) {
			this.inherited(arguments); // for the 'state' handling
			return this._timeBox.setValid(isValid, message);
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


