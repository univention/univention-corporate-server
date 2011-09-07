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

	name: '',

	label: '',

	required: '',

	disabled: false,

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcPasswordInputBox',

	_firstWidget: null,

	_secondWidget: null,

	buildRendering: function() {
		this.inherited(arguments);

		// create password fields
		this._firstWidget = this.adopt(umc.widgets.PasswordBox, {
			required: this.required,
			disabled: this.disabled,
			name: '__' + this.name, // '__' will exclude the entry from umc.widgets.Form.gatherFormValues()
			validator: dojo.hitch(this, '_checkValidity', 1)
		});
		this._secondWidget = this.adopt(umc.widgets.PasswordBox, {
			required: this.required,
			disabled: this.disabled,
			label: this._('%(label)s (retype)', this),
			name: this.name,
			validator: dojo.hitch(this, '_checkValidity', 2),
			invalidMessage: this._('The passwords do not match, please retype again.')
		});

		// register to 'onChange' events
		this.connect(this._secondWidget, 'onChange', 'onChange');

		// create layout
		var container = this.adopt(umc.widgets.ContainerWidget, {});
		this.addChild(container);
		container.addChild(this._firstWidget);

		container = this.adopt(umc.widgets.ContainerWidget, {});
		this.addChild(container);
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
		return this._secondWidget.get('value');
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
	}
});


