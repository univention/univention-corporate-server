/*
 * Copyright 2011-2012 Univention GmbH
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

	// system-setup-boot
	wizard_mode: false,

	// __systemsetup__ user is logged in at local firefox session
	local_mode: false,

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// internal flag whether setValues() has been called at least once or not
	_firstSetValues: true,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Language');
		this.headerText = this._('Language settings');
		this.helpText = this._('<i>Language settings</i> incorporate all language relevant configurations, such as time zone, keyboard layout, and system locales.');
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
			dynamicValues: 'setup/lang/keymaps',
			onChange: dojo.hitch(this, function() {
				if(this.local_mode) {
					this.umcpCommand('setup/keymap/save', {keymap: this._form.gatherFormValues()['locale/keymap']});
				}
			})
		}, {
			type: 'MultiObjectSelect',
			name: 'locale',
			label: this._('Installed system locales'),
			queryCommand: dojo.hitch(this, function(options) {
				return this.umcpCommand('setup/lang/locales', options).then(function(data) {
					return data.result;
				});
			}),
			queryWidgets: [{
				type: 'ComboBox',
				name: 'category',
				label: this._('Category'),
				value: 'language_en',
				staticValues: [
					{id: 'language_en', label: this._('Language (english)')},
					{id: 'language', label: this._('Language')},
					{id: 'langcode', label: this._('Language code')},
					{id: 'countrycode', label: this._('Country code')}
				]
			}, {
				type: 'TextBox',
				name: 'pattern',
				value: '*',
				label: this._('Name')
			}],
			autosearch: true,
			height: '200px'
		}, {
			type: 'ComboBox',
			name: 'locale/default',
			label: this._('Default system locale'),
			depends: 'locale',
			umcpCommand: this.umcpCommand,
			dynamicValues: dojo.hitch(this, function(vals) {
				return this._form.getWidget('locale').get('value');
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

//		FIXME: fix depends entry in MultiObjectSelect
//		dojo.connect(this._form._widgets.locale._multiSelect, 'onChange', dojo.hitch(this, function() {
//			this._form.getWidget('locale/default').set('staticValues', this.getValues()['locale']);
//		}));
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);
		if (this.wizard_mode && this._firstSetValues) {
			this._firstSetValues = false;
			var countrycode = null;
			var default_locale_default = null;
			if (dojo.locale && dojo.locale.split('-').length == 2) {
				var parts = dojo.locale.split('-');
				countrycode = parts[1].toLowerCase();
				default_locale_default = parts[0] + '_' + parts[1] + '.UTF-8:UTF-8';
			}
			if (vals.locale.indexOf(default_locale_default) < 0) {
				vals.locale.push(default_locale_default);
			}
			vals['locale/default'] = default_locale_default;
			this.umcpCommand('setup/lang/default_keymap', {
				'countrycode': countrycode
			}).then(dojo.hitch(this, function(data) { 
				this._form.getWidget('locale/keymap').set('value', data.result);
			}));
			this.umcpCommand('setup/lang/default_timezone', {
				'countrycode': countrycode
			}).then(dojo.hitch(this, function(data) { 
				this._form.getWidget('timezone').set('value', data.result);
			}));
		}
		this._form.setFormValues(vals);
	},

	getValues: function() {
		var vals = this._form.gatherFormValues();
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



