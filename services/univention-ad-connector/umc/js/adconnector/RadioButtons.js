/*
 * Copyright 2014-2019 Univention GmbH
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
	"dijit/form/RadioButton",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane"
], function(declare, lang, array, RadioButton, tools, _FormWidgetMixin, ContainerWidget, LabelPane) {
	return declare("umc.modules.adconnector.RadioButtons", [ ContainerWidget, _FormWidgetMixin ], {
		value: null,

		staticValues: null,

		_radioButtons: null,

		name: null,

		// the class name of the widget as CSS class
		'class': 'umcRadioButtons',

		postMixInProperties: function() {
			this.inherited(arguments);
			if (!this.staticValues) {
				this.staticValues = [];
			}
			this.valid = false;
			this.sizeClass = null;
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._radioButtons = [];
			array.forEach(this.staticValues, function(ientry, i) {
				var radioButton = new RadioButton({
					name: this.name,
					value: ientry.id,
					labelPosition: 'right'
				});
				this._radioButtons[i] = radioButton;
				var labelPane = new LabelPane({
					content: radioButton,
					label: ientry.label
				});
				radioButton.watch('checked', lang.hitch(this, function(attr, oldval, newval) {
					var value = radioButton.get('value');
					if (newval) {
						this.set('value', value);
						this.set('valid', true);
					}
				}));
				this.addChild(labelPane);
			}, this);
		},

		_setValueAttr: function(value) {
			array.some(this.staticValues, function(ientry, i) {
				if (value == ientry.id) {
					this._radioButtons[i].set('checked', true);
					this._set('value', value);

					// break loop
					return true;
				}
			}, this);
		},

		postCreate: function() {
			this.inherited(arguments);
		}
	});
});

