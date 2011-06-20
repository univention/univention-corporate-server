/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.udm");

dojo.require("umc.widgets.Module");
dojo.require("umc.tools");
/*dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.StandbyMixin");*/
dojo.require("umc.widgets.Grid");
dojo.require("umc.i18n");
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for handling UDM modules

	// the property field that acts as unique identifier
	idProperty: 'ldap-dn',

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

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
			isMultiAction: false
			//callback: dojo.hitch(this, function(vars) {
			//	if (vars.length) {
			//		this._detailDialog.loadVariable(vars[0]);
			//	}
			//})
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
		this.addChild(this._grid);
		this.layout();

		//
		// add search widget
		//

		var thisUmcpCommand = dojo.hitch(this, 'umcpCommand');
		var widgets = [{
			type: 'ComboBox',
			name: 'container',
			description: this._( 'The LDAP container in which the query is executed.' ),
			label: this._('Container'),
			value: 'all',
			staticValues: [ 
				{ id: 'all', label: this._( 'All containers' ) }
			],
			dynamicValues: 'udm/containers',
			umcpCommand: thisUmcpCommand
		}, {
			type: 'ComboBox',
			name: 'objectType',
			description: this._( 'The type of the LDAP object.' ),
			label: this._('Object type'),
			value: 'all',
			staticValues: [ 
				{ id: 'all', label: this._( 'All types' ) }
			],
			dynamicValues: 'udm/types',
			umcpCommand: thisUmcpCommand
		}, {
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Object property' ),
			value: 'any',
			staticValues: [
				{ id: 'any', label: this._( 'Any property' ) }
			],
			dynamicValues: 'udm/properties',
			umcpCommand: thisUmcpCommand,
			depends: 'objectType'
		}, {
			type: 'MixedInput',
			name: 'objectPropertyValue',
			description: this._( 'The value for the specified object property on which the query is filtered.' ),
			label: this._( 'Property value' ),
			dynamicValues: 'udm/values',
			depends: [ 'objectProperty', 'objectType' ]
		}];

		// generate the search widget
		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			onSearch: dojo.hitch(this._grid, 'filter')
		});
		this.addChild(this._searchWidget);
	}

});

