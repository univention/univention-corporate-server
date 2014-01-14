/*
 * Copyright 2011-2014 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/MultiSelect",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, Form, Page, MultiSelect, _) {

	return declare("umc.modules.setup.SoftwarePage", [ Page ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		umcpCommand: tools.umcpCommand,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		_orgComponents: undefined,

		_noteShowed: false,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('Software');
			this.headerText = _('Software settings');
			this.helpText = _('Via the <i>software settings</i>, particular software components may be installed or removed.');
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: MultiSelect,
				name: 'components',
				label: _('Installed software components'),
				umcpCommand: this.umcpCommand,
				dynamicValues: 'setup/software/components',
				dynamicOptions: {},
				sortDynamicValues: false,
				style: 'width: 500px;',
				height: '200px'
			}];

			var layout = [{
				label: _('Installation of software components'),
				layout: ['components']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this.addChild(this._form);

			// show notes when samba 3/4 is selected
			this.own(this._form.getWidget('components').watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				array.forEach(['samba', 'samba4'], function(ikey) {
					var r = new RegExp('univention-' + ikey + '\\b');
					if (array.some(this._getInstalledComponents(), function(icomponent) { return  (r.test(icomponent)); }, this)) {
						this._showNote(ikey);
					}
				}, this);
			})));

			// show notes for changes in the software settings
			this.own(this._form.getWidget('components').watch('value', lang.hitch(this, function() {
				this._showNote('software');
			})));

			// remember which notes have already been shown
			this._noteShowed = { };
			this._myNotes = {
				samba: _('It is not possible to mix NT and Active Directory compatible domaincontroller. Make sure the existing UCS domain is NT-compatible (Samba 3).'),
				samba4: _('It is not possible to mix NT and Active Directory compatible domaincontroller. Make sure the existing UCS domain is Active Directory-compatible (Samba 4).'),
				software: _('Installing or removing software components may result in restarting or stopping services. This can have severe side-effects when the system is in productive use at the moment.')
			};
		},

		_showNote: function(key) {
			if (!(key in this._noteShowed) || !this._form.getWidget('components').focused) {
				// make sure key exists
				return;
			}

			if (!this._noteShowed[key]) {
				this._noteShowed[key] = true;
				this.addWarning(this._myNotes[key]);
			}
		},

		setValues: function(vals) {
			// set dynamicOption to get list of components corresponding to selected system role
			this._form.getWidget('components').set('dynamicOptions', { role: vals['server/role'] });

			// get a dict of all installed components and initialise component list
			var components = (vals.components || '').split(/\s+/);
			this._form.getWidget('components').setInitialValue(components, true);

			if (this._orgComponents === undefined) {
				this._orgComponents = {};
				array.forEach(components, function(icomponent) {
					if(icomponent !== "") {
						this._orgComponents[icomponent] = true;
					}
				}, this);
			}

			// handling of notes
			this._noteShowed = { };
			var role = vals['server/role'];
			if (role == 'domaincontroller_backup' || role == 'domaincontroller_slave') {
				// only show samba notes on backup/slave
				this._noteShowed.samba = false;
				this._noteShowed.samba4 = false;
			}
			// show note when changing software only on a joined system in productive mode
			this._noteShowed.software = this.wizard_mode;
		},

		getValues: function() {
			return {
				components: this._form.getWidget('components').get('value').join(' ')
			};
		},

		_getComponents: function() {
			// return a dict of currently selected components
			var components = {};
			array.forEach(this._form.get('value').components, function(icomp) {
				components[icomp] = true;
			});
			return components;
		},

		_getRemovedComponents: function() {
			// if a previously installed component has been deselected
			// -> uninstall all its packages
			var components = [];
			var selectedComponents = this._getComponents();
			tools.forIn(this._orgComponents, function(icomponent) {
				if (!(icomponent in selectedComponents)) {
					components.push(icomponent);
				}
			});
			return components;
		},

		_getInstalledComponents: function() {
			// if a previously not/partly installed component has been selected
			// -> install all its packages
			var components = [];
			tools.forIn(this._getComponents(), function(icomponent) {
				if (!(icomponent in this._orgComponents)) {
					components.push(icomponent);
				}
			}, this);
			return components;
		},

		getSummary: function() {
			// a list of all components with their labels
			var allComponents = {};
			array.forEach(this._form.getWidget('components').getAllItems(), function(iitem) {
				allComponents[iitem.id] = iitem.label;
			});

			// get changed components
			var removeComponents = this._getRemovedComponents();
			var installComponents = this._getInstalledComponents();

			// get a (verbose) list of components that will be removed/installed
			var result = [];
			var components = [];
			if (installComponents.length) {
				components = array.map(installComponents, function(icomponent) {
					return allComponents[icomponent];
				});
				result.push({
					variables: ['components'],
					description: _('Installing software components'),
					values: components.join(', ')
				});
			}
			if (removeComponents.length) {
				components = array.map(removeComponents, function(icomponent) {
					return allComponents[icomponent];
				});
				result.push({
					variables: ['components'],
					description: _('Removing software components'),
					values: components.join(', ')
				});

			}
			return result;
		},

		onSave: function() {
			// event stub
		}
	});
});
