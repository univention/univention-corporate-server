/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.udm");

dojo.require("dojo.DeferredList");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.TabContainer");
dojo.require("umc.widgets.Module");
dojo.require("umc.tools");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.i18n");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.GroupBox");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for handling UDM modules

	// the property field that acts as unique identifier
	idProperty: 'ldap-dn',

	_searchPage: null,
	_detailForm: null,
	_detailTabs: null,

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		// render search page, we first need to query lists of containers/superodinates
		// in order to correctly render the search form
		(new dojo.DeferredList([
			this.umcpCommand('udm/containers'),
			this.umcpCommand('udm/superordinates')
		])).then(dojo.hitch(this, function(results) {
			var containers = results[0][0] ? results[0][1] : [];
			var superordinates = results[1][0] ? results[1][1] : [];
			this._renderSearchPage(containers.result, superordinates.result);
		}));
	},

	_renderSearchPage: function(containers, superordinates) {
		// setup search page
		this._searchPage = new dijit.layout.BorderContainer({});
		this.addChild(this._searchPage);

		//
		// add data grid
		//

		// define actions
		var actions = [{
			name: 'add',
			label: this._( 'Add' ),
			description: this._( 'Adding a new LDAP object.' ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true
			//callback: dojo.hitch(this, function() {
			//	this._detailDialog.newVariable();
			//})
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Edit the LDAP object.' ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids, items) {
				if (items.length && items[0].objectType) {
					// for the detail page, we first need to query property data from the server
					// for the layout of the selected object type, then we can render the page
					var params = { objectType: items[0].objectType };
					(new dojo.DeferredList([
						this.umcpCommand('udm/properties', params),
						this.umcpCommand('udm/layout', params)
					])).then(dojo.hitch(this, function(results) {
						var properties = results[0][1];
						var layout = results[1][1];
						this._renderDetailPage(properties.result, layout.result);
						this.showDetailPage();
					}));
				}
			})
		}, {
			name: 'delete',
			label: this._( 'Delete' ),
			description: this._( 'Deleting the selected LDAP object.' ),
			iconClass: 'dijitIconDelete'
			//callback: dojo.hitch(this, function(vars) {
			//	this.moduleStore.multiRemove(vars);
			//})
		}];

		// define grid columns
		var columns = [{
			name: 'name',
			label: this._( 'Name' ),
			description: this._( 'Name of the LDAP object.' ),
			editable: false
		}, {
			name: 'path',
			label: this._('Path'),
			description: this._( 'Path of the LDAP object.' )
		}];

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore
		});
		this._searchPage.addChild(this._grid);

		//
		// add search widget
		//
		
		var umcpCmd = dojo.hitch(this, 'umcpCommand');
		var widgets = [];
		var layout = [];
		
		// check whether we need to display containers or superordinates
		var objTypeDependencies = [];
		var objTypes = [];
		if (superordinates.length) {
			// superordinates...
			widgets.push({
				type: 'ComboBox',
				name: 'superordinate',
				description: this._( 'The superordinate in which the search is carried out.' ),
				label: this._('Superordinate'),
				value: superordinates[0].id || superordinates[0],
				staticValues: superordinates,
				umcpCommand: umcpCmd
			});
			layout.push('superordinate');
			objTypeDependencies.push('superordinate');
		}
		else {
			// containers...
			containers.unshift({ id: 'all', label: this._( 'All containers' ) });
			widgets.push({
				type: 'ComboBox',
				name: 'container',
				description: this._( 'The LDAP container in which the query is executed.' ),
				label: this._('Container'),
				value: containers[0].id || containers[0],
				staticValues: containers,
				umcpCommand: umcpCmd
			});
			layout.push('container');
			objTypes.push({ id: this.moduleFlavor, label: this._( 'All types' ) });
		}

		// add remaining elements of the search form
		widgets = widgets.concat([{
			type: 'ComboBox',
			name: 'objectType',
			description: this._( 'The type of the LDAP object.' ),
			label: this._('Object type'),
			value: objTypes.length ? this.moduleFlavor : undefined,
			staticValues: objTypes,
			dynamicValues: 'udm/types',
			umcpCommand: umcpCmd,
			depends: objTypeDependencies
		}, {
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Object property' ),
			dynamicValues: 'udm/properties',
			dynamicOptions: { searchable: true },
			umcpCommand: umcpCmd,
			depends: 'objectType'
		}, {
			type: 'MixedInput',
			name: 'objectPropertyValue',
			description: this._( 'The value for the specified object property on which the query is filtered.' ),
			label: this._( 'Property value' ),
			dynamicValues: 'udm/values',
			umcpCommand: umcpCmd,
			depends: [ 'objectProperty', 'objectType' ]
		}]);
		layout = layout.concat([ 'objectType', 'objectProperty', 'objectPropertyValue' ]);

		// generate the search widget
		this._searchWidget = new umc.widgets.SearchForm({
			widgets: widgets,
			layout: [ layout ],
			onSearch: dojo.hitch(this._grid, 'filter')
		});
		var group = new umc.widgets.GroupBox({
			legend: this._('Filter results'),
			region: 'top',
			toggleable: false,
			content: this._searchWidget
		});
		this._searchPage.addChild(group);
	},

	_renderDetailPage: function(properties, layoutSubTabs) {
		// create detail page
		this._detailTabs = new dijit.layout.TabContainer({
			nested: true,
			region: 'center'
		});

		// render all widgets
		var widgets = umc.tools.renderWidgets(properties);

		// render the layout for each subtab
		dojo.forEach(layoutSubTabs, function(ilayout) {
			var subTab = new umc.widgets.Page({
				title: ilayout.label || ilayout.name //TODO: 'name' should not be necessary
			});
			subTab.addChild(umc.tools.renderLayout(ilayout.layout, widgets));
			this._detailTabs.addChild(subTab);
		}, this);
		this._detailTabs.startup();

		// setup detail page, needs to be wrapped by a form (for managing the
		// form entries) and a BorderContainer (for the footer with buttons)
		var layout = new dijit.layout.BorderContainer({});
		layout.addChild(this._detailTabs);

		// buttons
		var buttons = umc.tools.renderButtons([{
			name: 'save',
			label: this._('Save changes')
		}, {
			name: 'close',
			label: this._('Back to search'),
			callback: dojo.hitch(this, 'closeDetailPage')
		}]);
		var footer = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcNoBorder'
		});
		dojo.forEach(buttons._order, function(i) { 
			footer.addChild(i);
		});
		layout.addChild(footer);

		// create the form containing the whole BorderContainer as content and add 
		// the form as new 'page'
		this._detailForm = umc.widgets.Form({
			widgets: widgets,
			content: layout,
			moduleStore: this.moduleStore
		});
		this.addChild(this._detailForm);
	},

	showDetailPage: function() {
		this.selectChild(this._detailForm);
	},

	closeDetailPage: function() {
		if (this._detailForm) {
			this.closeChild(this._detailForm);
			this._detailForm = null;
			this._detailTabs = null;
		}
	},

	postCreate: function() {
		// only show the objectType combobox when there are different values to choose from
		/*var objTypeWidget = this._searchWidget._widgets.objectType;
		this.connect(objTypeWidget, 'onDynamicValuesLoaded', function(values) {
			if (values.length) {
				//dojo.style(objTypeWidget.
			}
		});*/
	}

});

