/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.LanguagePage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.LanguagePage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Language');
		this.headerText = this._('Language settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'ComboBox',
			name: 'timezone',
			label: this._('Time zone'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/lang/timezones'
		}, {
			type: 'ComboBox',
			name: 'locale/keymap',
			label: this._('Keyboard layout'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/lang/keymaps'
		}, {
			type: 'MultiSelect',
			name: 'locale',
			label: this._('Installed system locales'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/lang/locales',
			height: '200px'
		}, {
			type: 'ComboBox',
			name: 'locale/default',
			label: this._('Default system locale'),
			depends: 'locale',
			umcpCommand: this.umcpCommand,
			dynamicValues: dojo.hitch(this, function(vals) {
				return this._form.getWidget('locale').getSelectedItems();
			})
		}];

		var layout = [{
			label: this._('Time zone and keyboard settings'),
			layout: ['timezone', 'locale/keymap']
		}, {
			label: this._('Language settings'),
			layout: ['locale', 'locale/default']
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		this.addChild(this._form);
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);
		vals.locale = _vals.locale.split(/\s+/);
		this._form.setFormValues(vals);
	},

	getValues: function() {
		var vals = this._form.gatherFormValues();
		vals.locale = vals.locale.join(' ');
		return vals;
	},
	
	getSummary: function() {
		// a list of all components with their labels
		var allLocales = {};
		dojo.forEach(this._form.getWidget('locale').getAllItems(), function(iitem) {
			allLocales[iitem.id] = iitem.label;
		});

		// get a verbose list of all locales
		var locales = dojo.map(this._form.getWidget('locale').get('value'), function(ilocale) {
			return allLocales[ilocale];
		});
		
		var vals = this.getValues();
		return [{
			variables: ['timezone' ],
			description: this._('Time zone'),
			values: vals['timezone']
		}, {
			variables: ['locale/keymap' ],
			description: this._('Keyboard layout'),
			values: vals['locale/keymap']
		}, {
			variables: ['locale' ],
			description: this._('Installed system locales'),
			values: locales.join(', ')
		}, {
			variables: ['locale/default' ],
			description: this._('Default system locale'),
			values: allLocales[vals['locale/default']]
		}];
	},

	onSave: function() {
		// event stub
	}
});



