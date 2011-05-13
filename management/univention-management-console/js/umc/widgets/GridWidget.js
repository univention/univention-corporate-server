/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.GridWidget");

dojo.require("dojox.grid.EnhancedGrid");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("umc.tools");

dojo.declare("umc.widgets.GridWidget", dijit.layout.BorderContainer, {
	// summary:
	//		Encapsulates a complex grid with store, UMCP commands and action buttons;
	//		offers easy access to select items etc.

	buttons: null,

	// umcpGet: String
	//		UMCP command for querying data to fill the form.
	umcpGetCommand: '',

	// umcpSet: String
	//		UMCP command for saving data from the form.
	umcpSetCommand: '',

	_widgets: null,

	_buttons: null,

	_layoutContainer: null,

	'class': 'umcNoBorder',

	buildRendering: function() {
		this.inherited(arguments);

		// create store
		this._store = new dojo.data.ItemFileWriteStore({ data: {items:[]} });
		var gridLayout = [{
			field: 'key',
			name: 'UCR-Variable',
			width: 'auto'
		},{
			field: 'value',
			name: 'Wert',
			width: 'auto',
			editable: true
		}];
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			region: 'center',
			query: { key: '*', value: '*' },
			queryOptions: { ignoreCase: true },
			structure: gridLayout,
			clientSort: true,
			store: this._store,
			rowSelector: '2px',
			//sortFields: {
			//	attribute: 'variable',
			//	descending: true
			//},
			plugins : {
				menus:{ 
					cellMenu: this._cellMenu,
					selectedRegionMenu: this._selectMenu
				},
				indirectSelection: {
					headerSelector: true,
					name: 'Selection',
					width: '25px',
					styles: 'text-align: center;'
				}
			}
		});
		this._grid.setSortIndex(1);
		this.addChild(this._grid);

	},

	postCreate: function() {
		this.inherited(arguments);

	},

	umcpGet: function(/*Object*/ parameters) {
		// summary:
		//		Send off an UMCP query to the server for querying the data for the form.
		//		For this the field umcpGetCommand needs to be set.
		// parameters: Object
		//		Parameter object that is passed to the UMCP command.

		umc.tools.assert(this.umcpGetCommand, 'In order to query form data from the server, umcpGetCommand needs to be set');

		// query data from server
		umc.tools.umcpCommand(this.umcpGetCommand, parameters).then(dojo.hitch(this, function(_data) {
			var values = this.gatherFormValues();
			var data = dojo.mixin({}, parameters, _data._result);
			var newValues = {};

			// copy all the fields that exist in the form
			umc.tools.forIn(data, function(ival, ikey) {
				if (ikey in values) {
					newValues[ikey] = ival;
				}
			}, this);

			// set all values at once
			this.setFormValues(newValues);

			// fire event
			this.onUmcpGetDone(true);
		}), dojo.hitch(this, function(error) {
			// fore event also in error case
			this.onUmcpGetDone(false);
		}));
	},

	umcpSet: function() {
		// summary:
		//		Gather all form values and send them to the server via UMCP.
		//		For this, the field umcpSetCommand needs to be set.

		umc.tools.assert(this.umcpSetCommand, 'In order to query form data from the server, umcpGetCommand needs to be set');

		// sending the data to the server
		var values = this.gatherFormValues();
		umc.tools.umcpCommand(this.umcpSetCommand, values).then(dojo.hitch(this, function(data) {
			// fire event
			this.onUmcpSetDone(true);
		}), dojo.hitch(this, function(error) {
			// fore event also in error case
			this.onUmcpSetDone(false);
		}));
	},

	onUmcpSetDone: function() {
		// event stub
	},

	onUmcpGetDone: function() {
		// event stub
	}
});







