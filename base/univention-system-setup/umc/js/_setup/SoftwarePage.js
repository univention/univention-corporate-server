/*
 * Copyright 2011 Univention GmbH
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

dojo.provide("umc.modules._setup.SoftwarePage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.SoftwarePage", [ umc.widgets.Page, umc.i18n.Mixin ], {
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

		this.title = this._('Software');
		this.headerText = this._('Software settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'MultiSelect',
			name: 'components',
			label: this._('Installed software components'),
			umcpCommand: this.umcpCommand,
			dynamicValues: 'setup/software/components',
			sortDynamicValues: false,
			style: 'width: 500px;',
			height: '200px'
		}];

		var layout = [{
			label: this._('Installation of software components'),
			layout: ['components']
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		this.addChild(this._form);
	},

	setValues: function(vals) {
		// get a dict of all packages that are installed
		var installedPackages = {};
		dojo.forEach((vals.packages || '').split(/\s+/), function(ipackage) {
			installedPackages[ipackage] = true;
		});

		var components = this._form.getWidget('components');
		this.umcpCommand('setup/software/components').then(dojo.hitch(this, function(data) {
			// all form values have been loaded, we have also the list of components
			var installedComponents = [];
			dojo.forEach(data.result, function(icomponent) {
				// a component is installed if all its packages are installed on the system
				var componentPackagesInstalled = true;
				dojo.forEach(icomponent.packages, function(jpackage) {
					if (!(jpackage in installedPackages)) {
						componentPackagesInstalled = false;
					}
					return componentPackagesInstalled;
				});

				if (componentPackagesInstalled) {
					installedComponents.push(icomponent.id);
				}
			});

			// set the values
			components.setInitialValue(installedComponents, true);
		}));
	},

	getValues: function() {
		var packages = [];
		dojo.forEach(this._form.gatherFormValues().components, function(icomponent) {
			// each selected software component is a list of packages that
			// are separated with a ':'
			packages = packages.concat(icomponent.split(':'));
		});
		packages = packages.sort();
		return { packages: packages.join(' ') };
	},

	getSummary: function() {
		// a list of all components with their labels
		var allComponents = {};
		dojo.forEach(this._form.getWidget('components').getAllItems(), function(iitem) {
			allComponents[iitem.id] = iitem.label;
		});

		// get a (verbose) list of all installed components
		var components = dojo.map(this._form.gatherFormValues().components, function(icomponent) {
			return allComponents[icomponent];
		});

		return [{
			variables: ['packages'],
			description: this._('Installed software components'),
			values: components.join(', ')
		}];
	},

	onSave: function() {
		// event stub
	}
});



