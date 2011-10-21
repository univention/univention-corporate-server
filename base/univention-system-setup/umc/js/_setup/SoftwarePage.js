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

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	_loadingDone: null,

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
			dynamicValues: 'setup/software/components',
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
			onSubmit: dojo.hitch(this, 'onSave')
		});

		this.addChild(this._form);
	},

	setValues: function(vals) {
		// get a dict of all packages that are installed
		var installedPackages = {};
		dojo.forEach((vals.packages || '').split(/\s+/), function(ipackage) {
			installedPackages[ipackage] = true;
		});

		// We need a workaround here since values are set during reloading of 
		// the grid, we need to wait for onValuesLoaded.
		// In the grid, there should be a mechanism that takes care of that, 
		// e.g., a deferred object that executes after fetching
		// ... any setting of value will be chained to this deferred
		var components = this._form.getWidget('components');
		if (!this._loadingDone) {
			this._loadingDone = new dojo.Deferred();
		}
		umc.tools.umcpCommand('setup/software/components').then(dojo.hitch(this, function(data) {
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

			// set the value as soon as the grid has loaded its values
			this._loadingDone.then(dojo.hitch(this, function() {
				components.set('value', installedComponents);
			}));
		}));

		var handle = this.connect(components, 'onValuesLoaded', function() {
			this.disconnect(handle);

			// notify the deferred that the values are loaded
			this._loadingDone.resolve();
		});
	},

	getValues: function() {
		var packages = [];
		dojo.forEach(this._form.gatherFormValues().components, function(icomponent) {
			// each selected software component is a list of packages that
			// are separated with a ':'
			packages = packages.concat(icomponent.split(':'));
		});
		return { packages: packages.join(' ') };
	},

	onSave: function() {
		// event stub
	}
});



