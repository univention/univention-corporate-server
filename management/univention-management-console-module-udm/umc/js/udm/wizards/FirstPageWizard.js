/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, all, Deferred, tools, Wizard, _) {

	return declare("umc.modules.udm.wizards.FirstPageWizard", [ Wizard ], {

		types: null,
		containers: null,
		superordinates: null,
		templates: null,

		_canContinue: null, // deferred which indicates if any of the pages in this wizard should be displayed or not

		postMixInProperties: function() {
			this.inherited(arguments);
			this._canContinue = new Deferred();

			if (this.moduleFlavor == 'navigation') {
				this.pages = [this._getOptionSelectionPage(), this._getActiveDirectoryWarningPage()];
			} else {
				this.pages = [this._getActiveDirectoryWarningPage(), this._getOptionSelectionPage()];
			}
		},

		canContinue: function() {
			return this._canContinue;
		},

		buildRendering: function() {
			this.inherited(arguments);

			var form = this._pages['firstPage']._form;
			form.ready().then(lang.hitch(this, function() {
				var formNecessary = this.shouldShowOptionSelectionPage();
				var showADPage = this.shouldShowActiveDirectoryPage();

				if (formNecessary || showADPage) {
					this._canContinue.reject();
					if (!formNecessary) {
						this.hideOptionSelectionPage();
					}
					if (!showADPage) {
						this.hideActiveDirectoryPage();
					}
					if (formNecessary/* && showADPage (FIXME: the state could be incorrect)*/) {
						this.updateObjectType();
					}
				} else {
					this._canContinue.resolve();
					this._finish();
				}
			}));
		},

		updateObjectType: function() {
			// make sure that object type is consistent and AD page gets hidden
			// this is only necessary in navigation flavor because there the AD warning is the first page and varies on the selected object type
			var form = this._pages['firstPage']._form;
			var objectTypeWidget = form.getWidget('objectType');
			if (objectTypeWidget) {
				objectTypeWidget.watch('value', lang.hitch(this, function(name, old, objectType) {
					if (!objectType) {
						return;
					}
					if (this.shouldShowActiveDirectoryPage(objectType)) {
						this.showActiveDirectoryPage();
						this._updateActiveDirectoryWarningMessage();
					} else {
						this.hideActiveDirectoryPage();
					}
					this._updateButtons('firstPage');
					this._updateButtons('activeDirectoryPage');
				}));
			}
		},

		shouldShowOptionSelectionPage: function() {
			// we have to show the page if any of the widgets comboboxes (e.g. object type, position, ...)
			// has more than one possible choice
			var form = this._pages['firstPage']._form;
			var formNecessary = false;
			tools.forIn(form._widgets, function(iname, iwidget) {
				if (iwidget.getAllItems) { // ComboBox, but not HiddenInput
					var items = iwidget.getAllItems();
					if (items.length > 1) {
						formNecessary = true;
					}
				}
			});
			return formNecessary;
		},

		next: function(currentPage) {
			var next = this.inherited(arguments);
			if (next) {
				if (!this._pages[next].get('disabled')) {
					return next;
				} else if (next !== currentPage) {
					var next2 = this.next(next);
					if (next2 !== next) {
						return next2;
					}
				}
			}
			return currentPage;
		},

		previous: function(currentPage) {
			var prev = this.inherited(arguments);
			if (prev) {
				if (!this._pages[prev].get('disabled')) {
					return prev;
				} else if (prev != currentPage) {
					var prev2 = this.previous(prev);
					if (prev2 !== prev) {
						return prev2;
					}
				}
			}
			return currentPage;
		},

		hasNext: function(currentPage) {
			return this.next(currentPage) != currentPage;
		},

		hasPrevious: function(currentPage) {
			return this.previous(currentPage) != currentPage;
		},

		hideOptionSelectionPage: function() {
			this._pages['firstPage'].set('disabled', true);
			this.selectChild(this._pages.activeDirectoryPage);
		},

		hideActiveDirectoryPage: function() {
			this._pages['activeDirectoryPage'].set('disabled', true);
			this.selectChild(this._pages.firstPage);
		},

		showActiveDirectoryPage: function() {
			this._pages['activeDirectoryPage'].set('disabled', false);
		},

		selectCorrectChild: function() {
			var formNecessary = this.shouldShowOptionSelectionPage();
			var showADPage = this.shouldShowActiveDirectoryPage();

			if (!formNecessary) {
				this.hideOptionSelectionPage();
			}
			if (!showADPage) {
				this.hideActiveDirectoryPage();
			}
			this._updateButtons('firstPage');
			this._updateButtons('activeDirectoryPage');
		},

		shouldShowActiveDirectoryPage: function() {
			var ucr = lang.getObject('umc.modules.udm.ucr', false) || {};
			var activeDirectoryEnabled = tools.isTrue(ucr['ad/member']);
			if (!activeDirectoryEnabled) {
				return false;
			}
			var objectType = this.getCurrentObjectType();
			var shouldShow = this.shouldShowActiveDirectoryPageFor(this.moduleFlavor);
			shouldShow = shouldShow || this.shouldShowActiveDirectoryPageFor(objectType);

			if (this.moduleFlavor === 'navigation') {
				var majorType = objectType.split('/')[0];
				tools.forIn(ucr, function(key, value) {
					if (new RegExp('^directory\/manager\/web\/modules\/' + majorType + '\/[^/]*\/show/adnotification$').test(key)) {
						shouldShow = shouldShow || tools.isTrue(value);
					}
				});
			}
			return shouldShow;
		},

		getCurrentObjectType: function() {
			var objectType = this.moduleFlavor;
			if (this._pages) {
				var form = this._pages['firstPage']._form;
				var objectTypeWidget = form.getWidget('objectType');
				if (objectTypeWidget) {
					objectType = objectTypeWidget.get('value');
				}
			}
			return objectType;
		},

		getCurrentObjectTypeName: function() {
			if (this.moduleFlavor !== 'navigation') {
				return this.objectNamePlural;
			}
			try {
				var o = this._pages['firstPage']._form.getWidget('objectType');
				return o._ids[o.get('value')].split(':')[0];
			} catch (error) {
				return this.objectNamePlural;
			}
		},

		shouldShowActiveDirectoryPageFor: function(objectType) {
			var ucr = lang.getObject('umc.modules.udm.ucr', false) || {};
			var enabledForCurrentObjectType = tools.isTrue(ucr['directory/manager/web/modules/' + objectType + '/show/adnotification']);
			return enabledForCurrentObjectType;
		},

		_getActiveDirectoryWarningPage: function() {
			var imageUrl = require.toUrl('dijit/themes/umc/icons/50x50/udm-ad-warning.png');
			var style = 'background-image: url(\'' + imageUrl + '\'); background-size: 100px; min-width: 100px;' +
				'min-height: 100px; background-repeat: no-repeat; padding-left: 100px; padding-top: 20px; margin: 0 1.5em; ';
			return {
				name: 'activeDirectoryPage',
				headerText: _('This UCS system is part of an Active Directory domain'),
				widgets: [{
					type: 'Text',
//					style: style,  // FIXME: somehow the style is set on two dom elements
					name: 'active_directory_warning',
					labelConf: { style: style },
					content: this._getActiveDirectoryWarningMessage()
				}]
			};
		},

		_getActiveDirectoryWarningMessage: function() {
			var objectName = this.getCurrentObjectTypeName();
			if (this.moduleFlavor == 'navigation') {
				return _('<b>Warning!</b>') + ' ' +
				_('Newly created LDAP objects of this type will only be available on UCS systems and not in the Active Directory domain.')  + ' ' +
				_('Please use the Active Directory administration utilities to create new domain LDAP objects of this type.') + ' ' +
				_('Press <i>Next</i> to create an LDAP object of this type only available on UCS systems.') +
				'<br/><br/>';
			} else {
				return _('<b>Warning!</b>') + ' ' +
				_('Newly created %s will only be available on UCS systems and not in the Active Directory domain.', objectName) + ' ' +
				_('Please use the Active Directory administration utilities to create new domain %s.', objectName) + ' ' +
				_('Press <i>Next</i> to create %s only available on UCS systems.', objectName) +
				'<br/><br/>';
			}
		},

		_updateActiveDirectoryWarningMessage: function() {
			try {
				this._pages.activeDirectoryPage._form.getWidget('active_directory_warning').set('content', this._getActiveDirectoryWarningMessage());
			} catch (error) {}
		},


		_getOptionSelectionPage: function() {
			var types = this.types, containers = this.containers, superordinates = this.superordinates, templates = lang.clone(this.templates);
			// depending on the list we get, create a form for adding
			// a new LDAP object
			var widgets = [];
			var layout = [];

			if ('navigation' != this.moduleFlavor) {
				// we need the container in any case
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					label: _('Container'),
					description: _('The container in which the LDAP object shall be created.'),
					visible: containers.length > 1,
					staticValues: containers,
					size: 'Two'
				});
				layout.push('container');

				if (superordinates.length) {
					// we have superordinates
					widgets.push({
						type: 'ComboBox',
						name: 'superordinate',
						label: _('Superordinate'),
						description: _('The corresponding superordinate for the LDAP object.'),
						staticValues: array.map(superordinates, function(superordinate) {
							return superordinate.title ? {id: superordinate.id, label: superordinate.title + ': ' + superordinate.label } : superordinate;
						}),
						visible: superordinates.length > 1,
						value: this.selectedSuperordinate,
						size: 'Two'
					}, {
						type: 'ComboBox',
						name: 'objectType',
						label: _('Type'),
						value: this.defaultObjectType,
						description: _('The exact object type of the new LDAP object.'),
						umcpCommand: this.umcpCommand,
						dynamicValues: lang.hitch(this, function(options) {
							return this.moduleCache.getChildModules(options.superordinate, null, true);
						}),
						depends: 'superordinate',
						size: 'Two'
					});
					layout.push('superordinate', 'objectType');
				} else {
					// no superordinates
					// object types
					if (types.length) {
						widgets.push({
							type: 'ComboBox',
							name: 'objectType',
							value: this.defaultObjectType,
							label: _('Type'),
							description: _('The exact object type of the new LDAP object.'),
							visible: types.length > 1,
							staticValues: types,
							size: 'Two'
						});
						layout.push('objectType');
					}

					// templates
					if (templates.length) {
						var initialValue = this.defaultObjectType;
						var defaultValue = null;
						if (initialValue) {
							var matchesDN = array.filter(templates, function(ielement) {
								return ielement.id == initialValue;
							});
							var matchesLabel = array.filter(templates, function(ielement) {
								return ielement.label.toLowerCase() == initialValue.toLowerCase();
							});
							if (matchesDN.length) {
								defaultValue = matchesDN[0].id;
							} else if (matchesLabel.length) {
								defaultValue = matchesLabel[0].id;
							} else {
								defaultValue = templates[0].id;
							}
						} else {
							defaultValue = templates[0].id;
						}
						templates.unshift({ id: 'None', label: _('None') });
						widgets.push({
							type: 'ComboBox',
							name: 'objectTemplate',
							value: defaultValue,  // see Bug #13073, for users/user, there exists only one object type
							label: _('%s template', tools.capitalize(this.objectNameSingular)),
							description: _('A template defines rules for default object properties.'),
							autoHide: true,
							staticValues: templates,
							size: 'Two'
						});
						layout.push('objectTemplate');
					}
				}
			} else {
				// for the navigation, we show all elements and let them query their content automatically
				widgets = [{
					type: 'HiddenInput',
					name: 'container',
					value: this.selectedContainer.id
				}, {
					type: 'Text',
					name: 'container_help',
					content: _('<p>The LDAP object will be created in the container:</p><p><i>%s</i></p>', this.selectedContainer.path || this.selectedContainer.label)
				}, {
					type: 'ComboBox',
					name: 'objectType',
					label: _('Type'),
					description: _('The exact object type of the new LDAP object.'),
					visible: types.length > 1,
					staticValues: types,
					size: 'Two'
				}, {
					type: 'ComboBox',
					name: 'objectTemplate',
					label: _('%s template', tools.capitalize(this.objectNameSingular)),
					description: _('A template defines rules for default object properties.'),
					depends: 'objectType',
					umcpCommand: this.umcpCommand,
					dynamicValues: lang.hitch(this, function(options) {
						return this.moduleCache.getTemplates(options.objectType);
					}),
					staticValues: [ { id: 'None', label: _('None') } ],
					autoHide: true,
					size: 'Two'
				}];
				layout = [ 'container', 'container_help', 'objectType', 'objectTemplate' ];
			}

			return {
				name: 'firstPage',
				widgets: widgets,
				layout: layout
			};
		},

		getValues: function() {
			var values = this.inherited(arguments);
			values.objectType = values.objectType || this.moduleFlavor;
			return values;
		},

		getObjectTypeName: function() {
			var firstPageValues = this.getValues();
			var objectTypeName;
			array.some(this.types, function(type) {
				if (type.id == firstPageValues.objectType) {
					objectTypeName = type.label;
					return true;
				}
			});
			if (!objectTypeName) {
				// cache may return empty label for no sub modules
				objectTypeName = this.objectNameSingular;
			}
			return objectTypeName;
		},

		focusFirstWidget: function(pageName) {
			return;
			// TODO: needs consistency? (check which pages are displayed)
			if (this.selectedChildWidget != this._pages.firstPage) {
				return;
			}
			var buttons = this._pages[pageName]._footerButtons;
			buttons.finish.focus();
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, lang.hitch(this, function(button) {
				if (button.name === 'finish') {
					button.label = _('Next');
				}
			}));
			return buttons;
		}
	});
});
