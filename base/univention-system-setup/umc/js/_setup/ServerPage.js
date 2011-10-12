/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.ServerPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.ServerPage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Server');
		this.headerText = this._('Server settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'fqdn',
			label: this._('Fully qualified domain name (e.g., master.example.com)')
		}, {
			type: 'TextBox',
			name: 'ldap/base',
			label: this._('LDAP base')
		}, {
			type: 'TextBox',
			name: 'windows/domain',
			label: this._('Windows domain')
		}, {
			type: 'PasswordInputBox',
			name: 'root_password',
			label: this._('Root password')
		}];

		var layout = [{
			label: this._('Host and domain settings'),
			layout: ['fqdn', 'ldap/base', 'windows/domain']
		}, {
			label: this._('Access settings'),
			layout: ['root_password']
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave')
		});

		this.addChild(this._form);
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);
		vals.fqdn = vals.hostname + '.' + vals.domainname;
		this._form.setFormValues(vals);
	},

	getValues: function() {
		var vals = this._form.gatherFormValues();
		var parts = vals.fqdn.split('.');
		vals.hostname = dojo.isString(parts[0]) ? parts[0] : '';
		vals.domainname = parts.slice(1).join('.');
		delete vals.fqdn;
		return vals;
	},

	onSave: function() {
		// event stub
	}
});



