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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/i18n/tools",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiObjectSelect",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, i18nTools, Page, Form, TextBox, ComboBox, MultiObjectSelect, _) {

	return declare("umc.modules.setup.LanguagePage", [ Page ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			//this.title = _('Language');
			//this.headerText = _('Language settings');
			//this.helpText = _('<i>Language settings</i> incorporate all language relevant configurations, such as time zone, keyboard layout, and system locales.');
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._localesDeferred = this.umcpCommand('setup/lang/locales', { pattern: "*" }).then(function(data) {
				var result = {};
				array.forEach(data.result, function(ientry) {
					result[ientry.id] = ientry.label;
				});
				return result;
			});

			var widgets = [{
				type: ComboBox,
				name: 'timezone',
				label: _('Time zone'),
				umcpCommand: this.umcpCommand,
				dynamicValues: 'setup/lang/timezones'
			}, {
				type: ComboBox,
				name: 'xorg/keyboard/options/XkbModel',
				label: _('Keyboard model'),
				umcpCommand: this.umcpCommand,
				dynamicValues: 'setup/lang/keyboard/model'
			}, {
				type: ComboBox,
				name: 'xorg/keyboard/options/XkbLayout',
				label: _('Keyboard layout'),
				umcpCommand: this.umcpCommand,
				dynamicValues: 'setup/lang/keyboard/layout',
			}, {
				type: ComboBox,
				name: 'xorg/keyboard/options/XkbVariant',
				label: _('Keyboard variant'),
				umcpCommand: this.umcpCommand,
				depends: 'xorg/keyboard/options/XkbLayout',
				dynamicValues: 'setup/lang/keyboard/variant',
				dynamicOptions: function(options) {
					// simple map from 'xorg/keyboard/options/XkbLayout' to the parameter
					// 'keyboardlayout' which is expected by the backend method
					return {
						keyboardlayout: options['xorg/keyboard/options/XkbLayout']
					};
				}
			}, {
				type: MultiObjectSelect,
				name: 'locale',
				label: _('Installed system locales'),
				queryCommand: lang.hitch(this, function(options) {
					return this.umcpCommand('setup/lang/locales', options).then(function(data) {
						return data.result;
					});
				}),
				queryWidgets: [{
					type: ComboBox,
					name: 'category',
					label: _('Category'),
					value: 'language_en',
					staticValues: [
						{id: 'language_en', label: _('Language (english)')},
						{id: 'language', label: _('Language')},
						{id: 'langcode', label: _('Language code')},
						{id: 'countrycode', label: _('Country code')}
					]
				}, {
					type: TextBox,
					name: 'pattern',
					value: '*',
					label: _('Name')
				}],
				formatter: lang.hitch(this, function(ids) {
					return this._localesDeferred.then(function(locales) {
						return array.map(ids, function(id) {
							if (typeof id == "string") {
								// label is the one from server or the id
								// itself (if locale is not chosable known
								// as available locale, e.g. "en_US:ISO-8859-1")
								return { id: id, label: locales[id] || id };
							}
							return id;
						});
					});
				}),
				autosearch: true,
				height: '200px'
			}, {
				type: ComboBox,
				name: 'locale/default',
				label: _('Default system locale'),
				depends: 'locale',
				umcpCommand: this.umcpCommand,
				dynamicValues: lang.hitch(this, function(vals) {
					return this._form.getWidget('locale').getAllItems();
				})
			}];

			var layout = [{
				label: _('Time zone and keyboard settings'),
				layout: ['timezone', 'xorg/keyboard/options/XkbModel', 'xorg/keyboard/options/XkbLayout', 'xorg/keyboard/options/XkbVariant']
			}, {
				label: _('Language settings'),
				layout: ['locale', 'locale/default']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this.own(this._form.getWidget('locale/default').watch('value', lang.hitch(this, function(name, old, value) {
				if (value) {
					this.onValuesChanged();
				}
			})));

			this.addChild(this._form);

		},

		setValues: function(_vals) {
			var vals = lang.mixin({}, _vals);
			var default_locale_default;
			vals.locale = vals.locale.split(/\s+/);
			this._form.setFormValues(vals);
		},

		getValues: function() {
			var vals = this._form.get('value');
			vals.locale = vals.locale.join(' ');
			return vals;
		},

		getSummary: function() {
			// a list of all components with their labels
			var allLocales = {};
			array.forEach(this._form.getWidget('locale').getAllItems(), function(iitem) {
				allLocales[iitem.id] = iitem.label;
			});

			// get a verbose list of all locales
			var locales = array.map(this._form.getWidget('locale').get('value'), function(ilocale) {
				return allLocales[ilocale];
			});
			
			var vals = this.getValues();
			return [{
				variables: ['timezone' ],
				description: _('Time zone'),
				values: vals['timezone']
			}, {
				variables: ['xorg/keyboard/options/XkbModel'],
				description: _('Keyboard model'),
				values: vals['xorg/keyboard/options/XkbModel']
			}, {
				variables: ['xorg/keyboard/options/XkbLayout'],
				description: _('Keyboard layout'),
				values: vals['xorg/keyboard/options/XkbLayout']
			}, {
				variables: ['xorg/keyboard/options/XkbVariant'],
				description: _('Keyboard variant'),
				values: vals['xorg/keyboard/options/XkbVariant']
			}, {
				variables: ['locale' ],
				description: _('Installed system locales'),
				values: locales.join(', ')
			}, {
				variables: ['locale/default' ],
				description: _('Default system locale'),
				values: allLocales[vals['locale/default']]
			}];
		},

		onValuesChanged: function() {
			// event stub
		},

		onSave: function() {
			// event stub
		}
	});
});
