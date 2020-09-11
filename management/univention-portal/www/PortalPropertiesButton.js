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
 * @module portal/PortalPropertiesButton
 */
define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"dojo/when",
	"dojo/Deferred",
	"dijit/popup",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/focus",
	"dijit/a11y",
	"dijit/form/Button",
	"dijit/form/ToggleButton",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Form",
	"umc/store",
	"umc/render",
	"umc/tools",
	"umc/dialog",
	"umc/i18n/tools",
	"put-selector/put",
	"./standby",
	"./portalContent",
	"./properties",
	"umc/i18n!portal",
], function(
	declare, array, lang, domClass, on, when, Deferred, popup, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin,
	dijitFocus, a11y, Button, ToggleButton, ContainerWidget, Form, store, render, tools, dialog, i18nTools, put, standby,
	portalContent, properties, _
) {
	var locale = i18nTools.defaultLang().replace(/-/, '_');
	var PortalPropertiesForm = declare("PortalPropertiesForm", [Form], {
		saveInitialFormValues: async function() {
			await this.ready();
			this._initialFormValues = this.get('value');

			// if we edit the displayName property of the portal
			// we only want to show the available languages (the languages that are also in the menu)
			// with the language codes prefilled.
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

		listen: async function() {
			// logo
			const logoWidget = this._widgets.logo;
			logoWidget.watch('value', (_name, _oldVal, newVal) => {
				if (newVal) {
					newVal = logoWidget.getDataUri(newVal);
				}
				this.onPropChanged('portalLogo', newVal);
			});


			// displayName
			const displayNameWidget = this._widgets.displayName;
			await displayNameWidget.ready();
			for (const row of displayNameWidget._widgets) {
				row[1].set('intermediateChanges', true);
			}
			displayNameWidget.watch('value', (_name, _oldVal, newVal) => {
				// newVal has the following format where
				// the current locale (selected language for the portal)
				// is the first entry
				//   [
				//   	['de_DE', 'Text']
				//   	['fr_FR', '']
				//   	['en_EN', 'Text']
				//   ]
				//
				// So we take the first row with text as preview value
				// since the current locale is at the start
				let previewText = '';
				const firstRowWithText = newVal.find(row => row[1]);
				if (firstRowWithText) {
					previewText = firstRowWithText[1];
				}
				this.onPropChanged('portalTitle', previewText);
			});

			// background
			const backgroundWidget = this._widgets.background;
			// await backgroundWidget.ready();
			backgroundWidget.watch('value', (_name, _oldVal, newVal) => {
				if (newVal) {
					newVal = backgroundWidget.getDataUri(newVal);
				}
				this.onPropChanged('portalBackground', newVal);
			});
		},

		_alteredValues() {
			var formValues = this.get('value');
			var alteredValues = {};
			tools.forIn(formValues, (iname, ivalue) => {
				if (iname === '$dn$') {
					return;
				}
				if (!tools.isEqual(ivalue, this._initialFormValues[iname])) {
					alteredValues[iname] = ivalue;
				}
			});
			return alteredValues;
		},

		hasChanges() {
			return Object.keys(this._alteredValues()).length > 0;
		},

		save: function() {
			const type = 'portals/portal';
			const dn = this._loadedID;
			const form = this;
			const initialFormValues = this._initialFormValues;

			var alteredValues = this._alteredValues();

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
				return;
			}

			var alteredValuesNonEmpty = {};
			tools.forIn(alteredValues, function(iname, ivalue) {
				if (!this._isEmptyValue(ivalue)) {
					alteredValuesNonEmpty[iname] = ivalue;
				}
			}, this);
			// validate the form values
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
					return;
				}

				// save the altered values
				if (alteredValues.displayName) {
					alteredValues.displayName = alteredValues.displayName.concat(initialFormValues.displayName_remaining);
				}

				var moduleStoreFunc = dn ? 'put' : 'add';
				var moduleStoreParams = dn ? lang.mixin(alteredValues, {'$dn$': dn}) : this.get('value');
				var moduleStoreOptions = dn ? null : {'objectType': type};
				return form.moduleStore[moduleStoreFunc](moduleStoreParams, moduleStoreOptions).then(lang.hitch(this, function(result) {
					if (result.success) {
						dialog.contextNotify(_('Changes saved'), {type: 'success'});
					} else {
						dialog.alert(_('The changes could not be saved: %(details)s', result));
					}
				}), function() {
					// TODO different error message
					dialog.alert(_('The changes could not be saved'));
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

		onPropChanged: function(propName, value) {}
	});
	var PortalPropertiesContainer = declare("PortalPropertiesContainer", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="portalProperties">
				<h1
					class="portalProperties__title"
					data-dojo-attach-point="titleNode"
				></h1>
				<div
					class="portalProperties__form"
					data-dojo-type="umc/widgets/ContainerWidget"
					data-dojo-attach-point="formContainer"
				></div>
				<div class="portalProperties__saveButtonWrapper">
					<button
						class="portalSidebarButton ucsPrimaryButton"
						data-dojo-type="dijit/form/Button"
						data-dojo-props="
							iconClass: 'iconSave',
							label: this._saveLabel,
							disabled: true,
						"
						data-dojo-attach-event="click: save"
						data-dojo-attach-point="saveButton"
					></button>
				</div>
			</div>
		`,

		_saveLabel: _('Save'),
		save: async function() {
			const hideStandby = standby.standby(this);
			await this._form.save();
			hideStandby();
		},

		title: _('Settings'),
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		open: false,
		_setOpenAttr: function(open) {
			domClass.toggle(this.domNode, 'portalProperties--open', open);
			this._set('open', open);
		},


		load: async function() {
			const dn = portalContent.portal().dn;
			const hideStandby = standby.standby(this);
			this.formContainer.destroyDescendants();
			const formConf = await properties.getFormConf('portals/portal', 
				['logo', 'displayName', 'background', 'portalComputers'], dn);
			const form = new PortalPropertiesForm(formConf);
			this._form = form;
			on(form, 'propChanged', (propName, value) => {
				this.saveButton.set('disabled', !form.hasChanges());
				this.onPropChanged(propName, value);
			});
			on(form, 'submit', () => {
				console.log('save');
			});
			await form.load(dn);
			this.formContainer.addChild(form);
			await form.saveInitialFormValues();
			await form.listen();
			hideStandby();
		},

		onPropChanged: function(propName, value) {},
	});


	return declare("PortalPropertiesButton", [ToggleButton], {
		showLabel: false,
		iconClass: 'iconGear',

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsIconButton');
		},

		_setCheckedAttr: function(checked) {
			this.portalPropertiesContainer.set('open', checked);
			this.inherited(arguments);
		},

		postCreate: function() {
			this.inherited(arguments);

			this.portalPropertiesContainer = new PortalPropertiesContainer({});
			document.body.appendChild(this.portalPropertiesContainer.domNode);
			this.portalPropertiesContainer.startup();
			on(this.portalPropertiesContainer, 'propChanged', (propName, value) => {
				this.onPropChanged(propName, value);
			});
		},

		load: function() {
			this.portalPropertiesContainer.load();
		},

		onPropChanged: function(propName, value) {}
	});
});
