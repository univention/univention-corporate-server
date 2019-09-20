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

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/PasswordBox",
	"umc/widgets/_FormWidgetMixin",
	"umc/i18n!"
], function(declare, array, lang, ContainerWidget, LabelPane, PasswordBox, _FormWidgetMixin, _) {
	return declare("umc.widgets.PasswordInputBox", [ ContainerWidget, _FormWidgetMixin ], {
		// summary:
		//		Simple widget that displays a widget/HTML code with a label above.

		displayLabel: false,

		name: '',

		label: '',

		required: '',

		disabled: false,

		// display the password boxes among each other
		twoRows: false,

		sizeClass: 'Two',

		// the widget's class name as CSS class
		baseClass: 'umcPasswordInputBox',

		_firstWidget: null,

		_secondWidget: null,

		_setLabelAttr: function(newLabel) {
			this.label = newLabel;
			if (this._firstWidget && this._secondWidget) {
				this._firstWidget.set('label', this.label);
				this._secondWidget.set('label', _('%(label)s (retype)', this));
			}
		},

		_setRequiredAttr: function(newVal) {
			this.required = newVal;
			if (this._firstWidget && this._secondWidget) {
				this._firstWidget.set('required', this.required);
				this._secondWidget.set('required', this.required);
			}
		},

		_setValueAttr: function(newVal) {
			this._firstWidget.set('value', newVal);
			this._secondWidget.set('value', newVal);
		},

		_setDisabledAttr: function(newVal) {
			this.disabled = newVal;
			if (this._firstWidget && this._secondWidget) {
				this._firstWidget.set('disabled', newVal);
				this._secondWidget.set('disabled', newVal);
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create password fields
			this._firstWidget = this.own(new PasswordBox({
				sizeClass: 'One',
				required: this.required,
				disabled: this.disabled,
				name: this.name + '_1',
				isValid: lang.hitch(this, '_checkValidity', 1),
				validator: lang.hitch(this, '_checkValidity', 1),
				invalidMessage: this.invalidMessage,
				pattern: this.pattern
			}))[0];
			this._secondWidget = this.own(new PasswordBox({
				sizeClass: 'One',
				required: this.required,
				disabled: this.disabled,
				name: this.name + '_2',
				isValid: lang.hitch(this, '_checkValidity', 2),
				validator: lang.hitch(this, '_checkValidity', 2),
				_isValidSubset: lang.hitch(this, '_checkValidity', 2),
				invalidMessage: _('The passwords do not match, please retype again.')
			}))[0];
			this._setLabelAttr(this.label);

			// register to value changes
			this.own(this._secondWidget.watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				this._set('value', newVal);
			})));

			// create layout
			var container = this.own(new ContainerWidget({}))[0];
			this.addChild(container);
			container.addChild(new LabelPane({
				content: this._firstWidget
			}));
			container.addChild(new ContainerWidget({
				style: 'height: 0;',
				'class': this.twoRows ? 'umcSize-One' : 'umcSize-One dijitDisplayNone'
			}));
			container.addChild(new LabelPane({
				content: this._secondWidget
			}));
			this.startup();
		},

		postCreate: function() {
			this.inherited(arguments);
			if (this.sizeClass == 'One') {
				this.sizeClass = 'Two';
			}

			// hook validate for the second box with the onChange event of the first one
			this.own(this._firstWidget.watch('value', lang.hitch(this, function() {
				this._secondWidget.validate(false);
			})));
			this.own(this._secondWidget.watch('value', lang.hitch(this, function() {
				this._firstWidget.validate(false);
			})));
		},

		_getValueAttr: function() {
			return this._firstWidget.get('value');
		},

		_checkValidity: function(ipwBox) {
			// make sure we can access the widgets
			if (!this._firstWidget || !this._secondWidget) {
				return true;
			}

			var pw1 = this._firstWidget.get('value');
			var pw2 = this._secondWidget.get('value');

			if (this.required === true && !pw1) {
				return false;
			}

			// always return true if the user is writing in the first box
			// and always return true for the first box
			if (this._firstWidget.focused || 1 == ipwBox) {
				return true;
			}

			// compare passwords
			if (!this._secondWidget.focused && pw1 != pw2) {
				// user stopped typing (i.e., no focus) and passwords do not match
				return false;
			}
			if (this._secondWidget.focused &&
					(pw2.length <= pw1.length && pw1.substr(0, pw2.length) != pw2) ||
					pw2.length > pw1.length) {
				// user is typing the second password and do not partly match
				return false;
			}
			return true;
		},

		validate: function() {
			this._firstWidget._hasBeenBlurred = this._hasBeenBlurred;
			this._firstWidget.validate();
			this._secondWidget._hasBeenBlurred = this._hasBeenBlurred;
			this._secondWidget.validate();
			return this.inherited(arguments);
		},

		setValid: function(isValid, message) {
			this._firstWidget.setValid(this._firstWidget.isValid(), message);
			this._secondWidget.setValid(this._secondWidget.isValid(), message);
			return this.inherited(arguments);
		},

		isValid: function() {
			// compare passwords
			var pw1 = this._firstWidget.get('value');
			var pw2 = this._secondWidget.get('value');
			return pw1 == pw2 && !(this.required === true && !pw1);
		},

		reset: function() {
			var widgets = [this._firstWidget, this._secondWidget];
			array.forEach(widgets, function(iwidget) {
				iwidget.reset();
			});
		},

		focus: function() {
			if (! this._firstWidget.get('value')) {
				this._firstWidget.focus();
			} else {
				this._secondWidget.focus();
			}
		}
	});
});

