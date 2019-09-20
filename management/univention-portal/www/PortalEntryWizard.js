/*
 * Copyright 2018-2019 Univention GmbH
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
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/when",
	"dojo/dom-class",
	"dijit/focus",
	"dijit/a11y",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	"umc/widgets/MultiInput",
	"umc/i18n/tools",
	"umc/i18n!portal"
], function(declare, lang, array, Deferred, all, when, domClass, dijitFocus, a11y, tools, dialog, Wizard, MultiInput, i18nTools, _) {
	return declare('PortalEntryWizard', [Wizard], {
		'class': 'portalEntryWizard',
		pageMainBootstrapClasses: 'col-xxs-12 col-xs-8',

		portalEntryProps: null,
		moduleStore: null,
		locale: null,

		initialFormValues: null,
		dn: null,

		_getWidgets: function(propNames) {
			return propNames.map(lang.hitch(this, function(propName) {
				return array.filter(this.portalEntryProps, function(iProp) {
					return iProp.id === propName;
				})[0];
			}));
		},

		ready: function() {
			var formDeferreds = [];
			tools.forIn(this._pages, function(pageName, page) {
				formDeferreds.push(page._form.ready());
			});
			return all(formDeferreds);
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.initialFormValues = {};
			this.dn = null;

			lang.mixin(this, {
				pages: [{
					name: 'name',
					widgets: this._getWidgets(['name', 'activated', 'allowedGroups']),
					layout: [['name'], ['activated'], ['allowedGroups']],
					headerText: ' ' // FIXME hacky workaround to get 'nav' to show so that Page.js adds the mainBootstrapClasses to 'main'
				}, {
					name: 'icon',
					widgets: this._getWidgets(['icon']),
					layout: ['icon'],
					headerText: ' '
				}, {
					name: 'displayName',
					widgets: this._getWidgets(['displayName']),
					layout: ['displayName'],
					headerText: ' '
				}, {
					name: 'link',
					widgets: this._getWidgets(['link']),
					layout: ['link'],
					headerText: ' '
				}, {
					name: 'description',
					widgets: this._getWidgets(['description']),
					layout: ['description'],
					headerText: ' '
				}]
			})
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.ready().then(lang.hitch(this, function() {
				this.getWidget('name', 'allowedGroups').autoSearch = true;

				// set the value of the displayName and description widget to
				// have the available languages (the ones that are available in the menu)
				// prefilled and do not allow the user to add or remove rows for languages
				var availableLanguageCodes = array.map(i18nTools.availableLanguages, function(ilanguage) {
					return ilanguage.id.replace(/-/, '_');
				});
				// shift current locale to the beginning
				availableLanguageCodes.splice(0, 0, availableLanguageCodes.splice(availableLanguageCodes.indexOf(this.locale), 1)[0]);

				var localizedPrefillValues = [];
				array.forEach(availableLanguageCodes, function(ilanguageCode) {
					localizedPrefillValues.push([ilanguageCode, '']);
				});
				array.forEach(['displayName', 'description'], lang.hitch(this, function(iname) {
					domClass.add(this.getWidget(iname).domNode, 'noRemoveButton');
					this.getWidget(iname).set('max', localizedPrefillValues.length);
					this.getWidget(iname).set('value', localizedPrefillValues);
					this.getWidget(iname).ready().then(lang.hitch(this, function() {
						array.forEach(this.getWidget(iname)._widgets, function(iwidget) {
							iwidget[0].set('disabled', true); // disable the textbox for the language code
						});
					}));
				}));

				// set initialFormValues
				array.forEach(this.pages, lang.hitch(this, function(ipage) {
					array.forEach(ipage.widgets, lang.hitch(this, function(iwidgetConf) {
						var widget = this.getWidget(iwidgetConf.id);
						var widgetReady = widget.ready ? widget.ready() : true;
						when(widgetReady).then(lang.hitch(this, function() {
							if (lang.exists('default', iwidgetConf)) {
								widget.set('value', iwidgetConf.default);
							}
							this.initialFormValues[iwidgetConf.id] = widget.get('value');
						}));
					}));
				}));
			}));
		},

		switchPage: function(pageName) {
			var scrollY = window.scrollY;
			this.inherited(arguments);
			window.scrollTo(0, scrollY);
		},

		getFooterButtons: function(pageName) {
			var footerbuttons = [{
				name: 'remove',
				label: _('Remove from this portal'),
				align: 'right',
				callback: lang.hitch(this, function() {
					dialog.confirm(_('Do you really want to remove this entry from this portal'), [{
						name: 'cancel',
						label: _('Cancel')
					}, {
						name: 'remove',
						label: _('Remove'),
						'default': true,
						callback: lang.hitch(this, 'onRemove')
					}]);
				})
			}, {
				name: 'previous',
				label: _('Back'),
				align: 'right',
				callback: lang.hitch(this, '_previous', pageName)
			}, {
				name: 'next',
				align: 'right',
				label: _('Next'),
				callback: lang.hitch(this, '_next', pageName)
			}, {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, 'onCancel')
			}, {
				name: 'save',
				defaultButton: true,
				label: _('Save'),
				callback: lang.hitch(this, '_finish', pageName)
			}, {
				name: 'finish',
				defaultButton: true,
				label: _('Finish'),
				callback: lang.hitch(this, '_finish', pageName)
			}];

			return footerbuttons;
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			var buttons = this._pages[pageName]._footerButtons;
			if (buttons.remove) {
				domClass.toggle(buttons.remove.domNode, 'dijitDisplayNone', this.dn && pageName === 'name' ? false : true);
			}
			if (buttons.finish) {
				domClass.toggle(buttons.finish.domNode, 'dijitDisplayNone', this.dn ? true : false || this.hasNext(pageName));
			}
			if (buttons.save) {
				domClass.toggle(buttons.save.domNode, 'dijitDisplayNone', this.dn ? false : true);
			}
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

		__validateWidget: function(widget) {
			if (widget instanceof MultiInput) {
				// FIXME the MultiInput widget does not implement validate.
				// this goes trough all widgets in all rows and validates them
				// so that the tooltip with the error message is shown.
				var i, j;
				for (i = 0; i < widget._widgets.length; ++i) {
					for (j = 0; j < widget._widgets[i].length; ++j) {
						var iwidget = widget._widgets[i][j];
						if (!iwidget.get('visible')) {
							// ignore hidden widgets
							continue;
						}
						iwidget._hasBeenBlurred = true;
						if (iwidget.validate !== undefined) {
							if (iwidget._maskValidSubsetError !== undefined) {
								iwidget._maskValidSubsetError = false;
							}
							iwidget.validate();
						}
					}
				}
			} else {
				widget.validate();
			}
		},

		_validatePage: function(pageName) {
			var deferred = new Deferred();
			var firstInvalidWidget = null;
			var initialFormValues = this.initialFormValues;
			var form = this.getPage(pageName)._form;
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

			var alteredValuesNonEmpty = {};
			tools.forIn(alteredValues, function(iname, ivalue) {
				if (!this._isEmptyValue(ivalue)) {
					alteredValuesNonEmpty[iname] = ivalue;
				}
			}, this);

			// reset validation settings from last validation
			tools.forIn(form._widgets, function(iname, iwidget) {
				if (iwidget.setValid) {
					iwidget.setValid(null);
				}
			});
			form.validate(); // validate all widgets to mark invalid/required fields

			// see if there are widgets that are required and have no value
			var allValid = true;
			tools.forIn(form._widgets, function(iname, iwidget) {
				var isEmpty = this._isEmptyValue(iwidget.get('value'));
				if (iwidget.required && isEmpty) {
					allValid = false;
					iwidget.setValid(false, _('This value is required'));
				} else if (!isEmpty && iwidget.isValid && !iwidget.isValid()) {
					allValid = false;
				}

				this.__validateWidget(iwidget);
				if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(iwidget.domNode)) {
					firstInvalidWidget = iwidget;
				}
			}, this);
			if (!allValid) {
				deferred.reject(firstInvalidWidget);
				return deferred;
			}

			// validate the form values
			tools.umcpCommand('udm/validate', {
				objectType: 'settings/portal_entry',
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
					this.__validateWidget(widget);
					if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(widget.domNode)) {
						firstInvalidWidget = widget;
					}
				}));
				if (!allValid) {
					deferred.reject(firstInvalidWidget);
				} else {
					deferred.resolve();
				}
			}));
			return deferred;
		},

		loadEntry: function(dn) {
			var deferred = new Deferred();
			this.ready().then(lang.hitch(this, function() {

			this.moduleStore.get(dn).then(lang.hitch(this, function(result) {
				this.dn = dn;
				this.loadedEntryPortals = result['portal'] || [];
				this.onLoadEntry();
				//// populate all widgets with the loaded portal entry data
				//// and store the initial form values
				array.forEach(this.pages, lang.hitch(this, function(ipage) {
					array.forEach(ipage.widgets, lang.hitch(this, function(iwidgetConf) {
						if (result[iwidgetConf.id]) {
							this.getWidget(iwidgetConf.id).set('value', result[iwidgetConf.id]);
							this.initialFormValues[iwidgetConf.id] = result[iwidgetConf.id];
						}
					}));
				}));

				//// we only want to show languages that are visible in the menu.
				//// separate languages that are in the menu and other lanuages and
				//// merge them back when saving
				var availableLanguageCodes = array.map(i18nTools.availableLanguages, function(ilanguage) {
					return ilanguage.id.replace(/-/, '_');
				});
				// shift current locale to the beginning
				availableLanguageCodes.splice(0, 0, availableLanguageCodes.splice(availableLanguageCodes.indexOf(this.locale), 1)[0]);

				array.forEach(['displayName', 'description'], lang.hitch(this, function(iname) {
					var filteredName = [];
					array.forEach(availableLanguageCodes, lang.hitch(this, function(ilanguageCode) {
						var name = array.filter(this.initialFormValues[iname], function(iname) {
							return iname[0] === ilanguageCode;
						})[0];
						if (!name) {
							name = [ilanguageCode, ''];
						}
						filteredName.push(name);
					}));
					var remainingName = array.filter(this.initialFormValues[iname], function(iname) {
						return array.indexOf(availableLanguageCodes, iname[0]) === -1;
					});

					this.initialFormValues[iname] = filteredName;
					this.initialFormValues[iname + '_remaining'] = remainingName;

					this.getWidget(iname).set('value', filteredName);
				}));

				this.onEntryLoaded();
				this._updateButtons(this.selectedChildWidget.name);
				deferred.resolve();
			}));
			}));
			return deferred;
		},
		onLoadEntry: function() {
			// event stub
		},
		onEntryLoaded: function() {
			// event stub
		},
		onNameQuery: function() {
			// event stub
		},
		onNameQueryEnd: function() {
			// event stub
		},

		_next: function(currentPage) {
			if (!currentPage) {
				this.inherited(arguments);
			} else {
				var origArgs = arguments;
				this._validatePage(currentPage).then(lang.hitch(this, function() {
					if (currentPage === 'name') {
						var enteredName = this.getWidget('name').get('value');
						this.onNameQuery();
						this.moduleStore.query({
							'objectProperty': 'name',
							'objectPropertyValue': enteredName
						}).then(lang.hitch(this, function(result) {
							if (!result.length) {
								this.inherited(origArgs);
								this.onNameQueryEnd();
							} else {
								var entryToLoad = array.filter(result, function(ientry) {
									return ientry.name === enteredName;
								})[0];
								if (!entryToLoad || (entryToLoad && this.dn && this.dn === entryToLoad['$dn$'])) {
									this.inherited(origArgs);
									this.onNameQueryEnd();
								} else {
									dialog.confirm(_('A portal entry with the given name already exists.'), [{
										'name': 'cancel',
										'label': _('Cancel'),
										'default': true
									}, {
										'name': 'load',
										'label': _('Load entry')
									}]).then(lang.hitch(this, function(choice) {
										if (choice === 'load') {
											this.loadEntry(entryToLoad['$dn$']).then(lang.hitch(this, function() {
												// if we load an existing portal entry we want to save the
												// portal and category attribute on the portal entry object
												// even if none of the loaded form values (e.g. displayName)
												// have changed.
												this._forceSave = true;
											}));
										} else {
											this.onNameQueryEnd();
										}
									}));
								}
							}
						}));
					} else {
						this.inherited(origArgs);
					}
				}), function(firstInvalidWidget) {
					dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
				});
			}
		},

		_finish: function(currentPage) {
			this._validatePage(currentPage).then(lang.hitch(this, function() {
				if (this.dn) {
					this.onSave(this.getValues());
				} else {
					this.onFinished(this.getValues());
				}
			}), function(firstInvalidWidget) {
				dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
			});
		},

		onSave: function(values) {
			// event stub
		},

		onRemove: function() {
			// stub
		}
	});
});
