/*
 * Copyright 2020 Univention GmbH
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

/**
 * @module portal/CategoryPropertiesDialog
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/dom-class",
	"dijit/focus",
	"dijit/a11y",
	"umc/tools",
	"umc/dialog",
	"umc/i18n/tools",
	"umc/widgets/Form",
	"./Dialog",
	"./properties",
	"./portalContent",
	"umc/i18n!portal",
], function(declare, lang, array, on, domClass, dijitFocus, a11y, tools, dialog, i18nTools, Form, Dialog, properties, portalContent, _) {
	const locale = i18nTools.defaultLang().replace(/-/, '_');
	const CategoryPropertiesForm = declare("CategoryPropertiesForm", [Form], {
		saveInitialFormValues: async function() {
			await this.ready();
			this._initialFormValues = this.get('value');

			//// Only show the available language with the language code field prefilled
			let availableLanguageCodes = i18nTools.availableLanguages.map(language => language.id.replace(/-/, '_'));
			// shift current locale to the beginning
			availableLanguageCodes.unshift(availableLanguageCodes.splice(availableLanguageCodes.indexOf(locale), 1)[0]);
			const filteredDisplayName = [];
			for (const languageCode of availableLanguageCodes) {
				let name = this._initialFormValues.displayName.find(name => name[0] === languageCode);
				if (!name) {
					name = [languageCode, ''];
				}
				filteredDisplayName.push(name);
			}
			this._initialFormValues['displayName_remaining'] = this._initialFormValues.displayName
				.filter(name => !availableLanguageCodes.includes(name[0]));
			this._initialFormValues.displayName = filteredDisplayName;
			// clear all rows then set max and then set filtered displayName
			const displayName = this._widgets.displayName;
			displayName.set('value', []);
			domClass.add(displayName.domNode, 'umcMultiInput--staticSize');
			displayName.set('max', filteredDisplayName.length);
			displayName.set('value', this._initialFormValues.displayName);
			// disable language code textboxes
			await displayName.ready();
			for (const widget of displayName._widgets) {
				widget[0].set('disabled', true);
			}
		},

		save: function() {
			const type = 'portals/category';
			const dn = this._loadedID;
			const form = this;
			const initialFormValues = this._initialFormValues;

			var formValues = form.get('value');

			var alteredValues = {};
			tools.forIn(formValues, function(iname, ivalue) {
				if (iname === '$dn$') {
					return;
				}
				if (!tools.isEqual(ivalue, initialFormValues[iname])) {
					alteredValues[iname] = ivalue;
				}
			});

			// reset validation settings from last validation
			tools.forIn(form._widgets, function(iname, iwidget) {
				if (iwidget.setValid) {
					iwidget.setValid(null);
				}
			});
			// see if there are widgets that are required and have no value
			var allValid = true;
			var firstInvalidWidget = null;
			tools.forIn(form._widgets, function(iname, iwidget) {
				var isEmpty = this._isEmptyValue(iwidget.get('value'));
				if (iwidget.required && isEmpty) {
					allValid = false;
					// TODO this is kind of doubled because form.validate()
					// is already called, but MultiInput widgets that are required
					// do not work correctly with validate
					iwidget.setValid(false, _('This value is required')); // TODO wording / translation
				} else if (iwidget.isValid && !iwidget.isValid()) {
					allValid = false;
				}
				if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(iwidget.domNode)) {
					firstInvalidWidget = iwidget;
				}
			}, this);
			if (!allValid) {
				dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
				return;
			}

			// check if the values in the form have changed
			// and if not return and close without saving
			if (Object.keys(alteredValues).length === 0) {
				this.hide();
				return;
			}

			var alteredValuesNonEmpty = {};
			tools.forIn(alteredValues, function(iname, ivalue) {
				if (!this._isEmptyValue(ivalue)) {
					alteredValuesNonEmpty[iname] = ivalue;
				}
			}, this);
			// validate the form values
			this.standby(true);
			return tools.umcpCommand('udm/validate', {
				objectType: type,
				properties: alteredValuesNonEmpty
			}).then(lang.hitch(this, function(response) {
				// parse response and mark widgets with invalid values
				var allValid = true;
				array.forEach(response.result, lang.hitch(this, function(iprop) {
					if (iprop.valid instanceof Array) {
						array.forEach(iprop.valid, function(ivalid, index) {
							if (ivalid) {
								iprop.valid[index] = null;
							} else {
								allValid = false;
							}
						});
					} else {
						if (iprop.valid) {
							iprop.valid = null;
						} else {
							allValid = false;
						}
					}

					var widget = form.getWidget(iprop.property);
					widget.setValid(iprop.valid, iprop.details);
					if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(widget.domNode)) {
						firstInvalidWidget = widget;
					}
				}));
				if (!allValid) {
					dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
					this.standby(false);
					return;
				}

				// save the altered values
				if (alteredValues.displayName) {
					alteredValues.displayName = alteredValues.displayName.concat(initialFormValues.displayName_remaining);
				}

				var moduleStoreFunc = dn ? 'put' : 'add';
				var moduleStoreParams = dn ? lang.mixin(alteredValues, {'$dn$': dn}) : formValues;
				var moduleStoreOptions = dn ? null : {'objectType': type};
				portalContent.modify('category', moduleStoreFunc, moduleStoreParams, moduleStoreOptions).then(() => {
					this.hide();
				}, () => {
					this.standby(false);
				});
			}));
		},
		_isEmptyValue: function(value) {
			if (typeof value === 'string' || value instanceof Array) {
				return value.length === 0;
			} else if (typeof value === 'object') {
				return Object.keys(value).length === 0;
			} else {
				return false;
			}
		},

		onSubmit() {
			this.save();
			return false;
		},
	});

	return declare("CategoryPropertiesDialog", [Dialog], {
		//// overwrites
		destroyAfterHide: true,
		noContentClass: 'umcDialog--empty',
		title: _('Edit category'),


		//// self
		category: null,
		save: function() {
			this._form.save();
		},

		load: async function() {
			this.standby(true);
			const formConf = await properties.getFormConf('portals/category', ['name', 'displayName'],
					this.category ? this.category.dn : null);
			const form = new CategoryPropertiesForm({
				...formConf,
				standby: lang.hitch(this, 'standby'),
				hide: lang.hitch(this, 'hide'),
			});
			this._form = form;
			if (this.category) {
				await form.load(this.category.dn);
			}
			await form.saveInitialFormValues();
			this.set('content', form);
			this.standby(false);
		},

		showAndLoad() {
			this.show();
			this.load();
		},

		remove() {
			this.standby(true);
			portalContent.removeCategory(this.category.idx).then(() => {
				this.hide();
			}, () => {
				this.standby(false);
			});
		},

		//// lifecycle
		constructor() {
			this.actions = [{
				$align: 'left',
				iconClass: 'iconX',
				class: 'ucsTextButton', 
				label: _('Cancel'),
				onClick: () => {
					this.onCancel();
				},
			}, {
				iconClass: 'iconSave',
				class: 'ucsTextButton',
				label: _('Save'),
				onClick: () => {
					this.save();
				}
			}];
		},

		postMixInProperties() {
			this.inherited(arguments);
			if (this.category) {
				this.actions.splice(1, 0, {
					$align: 'left',
					iconClass: 'iconTrash',
					class: 'ucsTextButton',
					label: _('Remove from this portal'),
					onClick: () => {
						this.remove();
					},
				});
			}
		},
	});
});
