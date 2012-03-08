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



