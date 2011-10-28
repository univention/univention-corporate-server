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

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	_noteShowed: false,

	_orgVals: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Certificate');
		this.headerText = this._('Certificate settings');
		this._orgVals = {};
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'ssl/common',
			label: this._('Common name for the root SSL certificate'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'ssl/lang/countrycodes'
		}, {
			type: 'ComboBox',
			name: 'ssl/country',
			label: this._('Country'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/lang/countrycodes'
		}, {
			type: 'TextBox',
			name: 'ssl/state',
			label: this._('State')
		}, {
			type: 'TextBox',
			name: 'ssl/locality',
			label: this._('Location')
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
			label: this._('Organization settings'),
			layout: [ 'ssl/organization', 'ssl/organizationalunit' ]
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		umc.tools.forIn(this._form._widgets, function(iname, iwidget) {
			this.connect(iwidget, 'onKeyUp', function() {
				if (iwidget.focused) {
					this._showNote();
				}
			});
			this.connect(iwidget, 'onChange', function() {
				if (iwidget.focused) {
					this._showNote();
				}
			});
		}, this);
		
		this.addChild(this._form);

		var countryWidget = this._form.getWidget('ssl/country');
		var _addCurrentCountry = function() {
			if (countryWidget.focused) {
				// ignore user changes
				return;
			}
			// make sure the country code is set
			if (!('ssl/country' in this._orgVals)) {
				return;
			}

			// see whether the current country code matches any country code in the list
			var val = this._orgVals['ssl/country'];
			var vals = countryWidget.getAllItems();
			var matches = dojo.filter(vals, function(ival) {
				return ival.id == val;
			});
			var staticValues = countryWidget.get('staticValues');
			var isInStaticValues = dojo.indexOf(staticValues, val) >= 0;
			if (!matches.length && !isInStaticValues) {
				// the current value set by the system is not in the list of country codes
				// we need to add the current value that is being set for backwards 
				// compatibility reasons
				countryWidget.set('staticValues', [ this._orgVals['ssl/country'] ]);
				countryWidget._loadValues();
			}
			else if (staticValues.length && !isInStaticValues) {
				// empty staticValues 
				countryWidget.set('staticValues', [ ]);
				countryWidget._loadValues();
			}
		};

		this.connect(countryWidget, 'onValuesLoaded', _addCurrentCountry);
		this.connect(countryWidget, 'onChange', _addCurrentCountry);
	},

	_showNote: function() {
		if (!this._noteShowed) {
			this._noteShowed = true;
			this.addNote(this._('Changes in the SSL certificate settings will result in generating new root SSL certificates. Note that this will require an update of all host certificates in the domain as the old root certificate is no longer valid.'));
		}
	},

	setValues: function(_vals) {
		this._form.setFormValues(_vals);
		this._orgVals = dojo.clone(_vals);
		this.clearNotes();
		this._noteShowed = false;
	},

	getValues: function() {
		return this._form.gatherFormValues();
	},

	getSummary: function() {
		// a list of all countries
		var allCountries = {};
		dojo.forEach(this._form.getWidget('ssl/country').getAllItems(), function(iitem) {
			allCountries[iitem.id] = iitem.label;
		});

		var vals = this.getValues();
		vals['ssl/country'] = allCountries[vals['ssl/country']];
		return [{
			variables: [/^ssl\/.*/],
			description: this._('SSL root certificate'),
			values: dojo.replace('{ssl/common}, {ssl/email}, {ssl/organization}, {ssl/organizationalunit}, {ssl/locality}, {ssl/state}, {ssl/country}', vals)
		}];
	},

	onSave: function() {
		// event stub
	}
});



