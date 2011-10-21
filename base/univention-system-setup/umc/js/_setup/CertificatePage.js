/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.CertificatePage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.CertificatePage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Certificate');
		this.headerText = this._('Certificate settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'ssl/common',
			label: this._('Common name for the root SSL certificate'),
			dynamicValues: 'ssl/lang/countrycodes'
		}, {
			type: 'ComboBox',
			name: 'ssl/country',
			label: this._('Country'),
			dynamicValues: 'setup/lang/countrycodes'
		}, {
			type: 'TextBox',
			name: 'ssl/state',
			label: this._('State')
		}, {
			type: 'TextBox',
			name: 'ssl/locality',
			label: this._('Locality')
		}, {
			type: 'TextBox',
			name: 'ssl/organization',
			label: this._('Organization')
		}, {
			type: 'TextBox',
			name: 'ssl/organizationalunit',
			label: this._('Business unit')
		}, {
			type: 'TextBox',
			name: 'ssl/email',
			label: this._('Email address')
		}];

		var layout = [{
			label: this._('General settings'),
			layout: [ 'ssl/common', 'ssl/email' ]
		}, {
			label: this._('Location settings'),
			layout: [ 'ssl/country', 'ssl/state', 'ssl/locality' ]
		}, {
			label: this._('Organisation settings'),
			layout: [ 'ssl/organization', 'ssl/organizationalunit' ]
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave')
		});

		this.addChild(this._form);
	},

	setValues: function(_vals) {
		this._form.setFormValues(_vals);
	},

	getValues: function() {
		return this._form.gatherFormValues();
	},

	onSave: function() {
		// event stub
	}
});



