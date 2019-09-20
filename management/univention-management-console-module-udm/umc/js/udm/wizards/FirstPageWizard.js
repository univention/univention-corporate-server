/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define,require*/

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

		showObjectType: true,
		showObjectTemplate: true,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._canContinue = new Deferred();

			if (this.moduleFlavor === 'navigation') {
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
			var _returnText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('users'),
					'groups/group'      : _('groups'),
					'computers/computer': _('computers'),
					'networks/network'  : _('network objects'),
					'dns/dns'           : _('DNS objects'),
					'dhcp/dhcp'         : _('DHCP objects'),
					'shares/share'      : _('shares'),
					'shares/print'      : _('printers'),
					'mail/mail'         : _('mail objects'),
					'nagios/nagios'     : _('Nagios objects'),
					'policies/policy'   : _('policies')
				}[this.moduleFlavor];
				if (!text) {
					text = _('LDAP objects');
				}
				return text;
			});

			if (this.moduleFlavor !== 'navigation') {
				return _returnText();
			}
			try {
				var o = this._pages['firstPage']._form.getWidget('objectType');
				return o._ids[o.get('value')].split(':')[0];
			} catch (error) {
				return _returnText();
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
			var _templateLabelText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('User template'),
					'groups/group'      : _('Group template'),
					'computers/computer': _('Computer template'),
					'networks/network'  : _('Network object template'),
					'dns/dns'           : _('DNS object template'),
					'dhcp/dhcp'         : _('DHCP object template'),
					'shares/share'      : _('Share template'),
					'shares/print'      : _('Printer template'),
					'mail/mail'         : _('Mail object template'),
					'nagios/nagios'     : _('Nagios object template'),
					'policies/policy'   : _('Policy template')
				}[this.moduleFlavor];
				if (!text) {
					text = _('LDAP object template');
				}
				return text;
			});

			var widgets = [];
			var layout = [];

			if (this.selectedSuperordinate && this.selectedSuperordinate.id) {
				// we have superordinates
				widgets.push({
					type: 'HiddenInput',
					name: 'superordinate',
					value: this.selectedSuperordinate.id
				}, {
					type: 'Text',
					name: 'superordinate_help',
					content: _('<p>The LDAP object will be created underneath of <i>%s</i>.</p>', this.selectedContainer.path || this.selectedSuperordinate.label)
				});
				layout.push('superordinate', 'superordinate_help');
			}

			layout.push('objectType');

			var selectedContainer = this.selectedContainer && this.selectedContainer.id;
			if (selectedContainer) {
				// a container is already selected in a tree
				widgets.push({
					type: 'HiddenInput',
					name: 'container',
					value: this.selectedContainer.id
				}, {
					type: 'Text',
					name: 'container_help',
					content: _('<p>The LDAP object will be created in the container:</p><p><i>%s</i></p>', this.selectedContainer.path || this.selectedContainer.label)
				});
				layout.push('container');
				if (!(~array.indexOf(layout, 'superordinate_help'))) {
					layout.push('container_help');
				}
			} else {
				// we need to select a container from default containers
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					label: _('Container'),
					description: _('The container in which the LDAP object shall be created.'),
					autoHide: true,
					depends: ['objectType'],
					dynamicValues: lang.hitch(this, function() {
						return this.moduleCache.getContainers(this.getWidget('objectType').get('value') || undefined).then(function(result) {
							result.sort(tools.cmpObjects('label'));
							return array.filter(result, function(icontainer) {
								return icontainer.id !== 'all';
							});
						});
					}),
					size: 'Two'
				});
				layout.push('container');
			}

			// object types
			if (!this.showObjectType && this.defaultObjectType) {
				widgets.push({
					type: 'HiddenInput',
					name: 'objectType',
					value: this.defaultObjectType
				});
			} else {
				widgets.push({
					type: 'ComboBox',
					name: 'objectType',
					value: this.defaultObjectType,
					label: _('Type'),
					description: _('The exact object type of the new LDAP object.'),
					autoHide: true,
					visible: this.showObjectType,
					//depends: (selectedContainer || this.moduleFlavor !== 'navigation') ? [] : ['container'/*, 'superordinate'*/],
					dynamicValues: lang.hitch(this, function() {
						var containerWidget = this.getWidget('firstPage', 'container');
						var superordinateWidget = this.getWidget('firstPage', 'superordinate');
						var container = containerWidget && containerWidget.get('value') || null;
						var superordinate = superordinateWidget && superordinateWidget.get('value') || null;
						if (superordinate) {
							container = null;
						}
						return this.moduleCache.getChildModules(superordinate, container, true).then(function(result) {
							result.sort(tools.cmpObjects('label'));
							return result;
						});
					}),
					size: 'Two'
				});
			}

			// templates
			if (this.showObjectTemplate) {
				widgets.push({
					type: 'ComboBox',
					name: 'objectTemplate',
					label: _templateLabelText(),
					description: _('A template defines rules for default object properties.'),
					value: this.defaultTemplate,
					depends: 'objectType',
					autoHide: true,
					visible: this.showObjectTemplate,
					umcpCommand: this.umcpCommand,
					dynamicValues: lang.hitch(this, function(options) {
						return this.moduleCache.getTemplates(options.objectType).then(function(result) {
							result.sort(tools.cmpObjects('label'));
							return result;
						});
					}),
					staticValues: [{id: 'None', label: _('None')}],
					size: 'Two'
				});
				layout.push('objectTemplate');
			} else {
				widgets.push({
					type: 'HiddenInput',
					name: 'objectTemplate',
					value: this.defaultTemplate
				});
			}

			if (this.moduleFlavor === 'navigation') {
				layout = ['container', 'container_help', 'objectType', 'objectTemplate'];
			}

			return {
				name: 'firstPage',
				widgets: widgets,
				layout: layout,
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				standbyOptions: {delay: 200},
				standby: lang.hitch(this, 'standby'),
			};
		},

		getValues: function() {
			var values = this.inherited(arguments);
			values.objectType = values.objectType || this.moduleFlavor;
			return values;
		},

		getObjectTypeName: function() {
			var _defaultObjectTypeNameText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('user'),
					'groups/group'      : _('group'),
					'computers/computer': _('computer'),
					'networks/network'  : _('network object'),
					'dns/dns'           : _('DNS object'),
					'dhcp/dhcp'         : _('DHCP object'),
					'shares/share'      : _('share'),
					'shares/print'      : _('printer'),
					'mail/mail'         : _('mail object'),
					'nagios/nagios'     : _('Nagios object'),
					'policies/policy'   : _('policy')
				}[this.moduleFlavor];
				if (!text) {
					text = _('LDAP object');
				}
				return text;
			});

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
				objectTypeName = _defaultObjectTypeNameText();
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
