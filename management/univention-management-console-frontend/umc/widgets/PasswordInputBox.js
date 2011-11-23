/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.PasswordInputBox");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.HiddenInput");
dojo.require("umc.widgets.LabelPane");
dojo.require("umc.widgets.PasswordBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.widgets.PasswordInputBox", [ 
	umc.widgets.ContainerWidget, 
	umc.widgets._FormWidgetMixin, 
	umc.widgets._WidgetsInWidgetsMixin,
	umc.i18n.Mixin 
], {
	// summary:
	//		Simple widget that displays a widget/HTML code with a label above.

	isLabelDisplayed: true,

	name: '',

	label: '',

	required: '',

	disabled: false,

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcPasswordInputBox',

	_firstWidget: null,

	_secondWidget: null,

	_setLabelAttr: function(newLabel) {
		this.label = newLabel;
		if (this._firstWidget && this._secondWidget) {
			this._firstWidget.set('label', this.label);
			this._secondWidget.set('label', this._('%(label)s (retype)', this));
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

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create password fields
		this._firstWidget = this.adopt(umc.widgets.PasswordBox, {
			required: this.required,
			disabled: this.disabled,
			name: this.name + '_1',
			validator: dojo.hitch(this, '_checkValidity', 1)
		});
		this._secondWidget = this.adopt(umc.widgets.PasswordBox, {
			required: this.required,
			disabled: this.disabled,
			name: this.name + '_2',
			validator: dojo.hitch(this, '_checkValidity', 2),
			invalidMessage: this._('The passwords do not match, please retype again.')
		});
		this._setLabelAttr(this.label);

		// register to 'onChange' events
		this.connect(this._secondWidget, 'onChange', 'onChange');

		// create layout
		var container = this.adopt(umc.widgets.ContainerWidget, {});
		this.addChild(container);
		container.addChild(new umc.widgets.LabelPane({
			content: this._firstWidget
		}));
		container.addChild(new umc.widgets.LabelPane({
			content: this._secondWidget
		}));
		this.startup();
	},

	postCreate: function() {
		this.inherited(arguments);

		// hook validate for the second box with the onChange event of the first one
		this.connect(this._firstWidget, 'onChange', dojo.hitch(this._secondWidget, 'validate', false));
	},

	_getValueAttr: function() {
		return this._firstWidget.get('value');
	},

	_checkValidity: function(ipwBox) {
		// make sure we can access the widgets
		if (!this._firstWidget || !this._secondWidget) {
			return true;
		}

		// always return true if the user is writing in the first box
		// and always return true for the first box
		if (this._firstWidget.focused || 1 == ipwBox) {
			return true;
		}

		// compare passwords
		var pw1 = this._firstWidget.get('value');
		var pw2 = this._secondWidget.get('value');
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

	isValid: function() {
		var res = this.inherited(arguments);
		if (undefined !== res && null !== res) {
			return res;
		}

		// compare passwords
		var pw1 = this._firstWidget.get('value');
		var pw2 = this._secondWidget.get('value');
		return pw1 == pw2 && !(this.required === true && !pw1);
	}
});


