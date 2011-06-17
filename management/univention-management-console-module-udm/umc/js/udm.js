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
			moduleStore: this.moduleStore,
			query: {
				container: "*",
				value: "*"
			}
		});
		this.addChild(this._grid);
		this.layout();

		//
		// add search widget
		//
	
		// we need to dynamically load the search widget
		this.umcpCommand('udm/query/layout').then(dojo.hitch(this, function(data) {
			// add to each widget a reference to the module specific umcpCommand method
			var widgets = data.result;
			dojo.forEach(widgets, dojo.hitch(this, function(iwidget) {
				if (iwidget && dojo.isObject(iwidget)) {
					iwidget.umcpCommand = dojo.hitch(this, 'umcpCommand');
				}
			}));

			// create the search widget
			this._searchWidget = new umc.widgets.SearchForm({
				region: 'top',
				widgets: widgets
			});
			this.addChild(this._searchWidget);
			this.layout();
		}));
	}

});

