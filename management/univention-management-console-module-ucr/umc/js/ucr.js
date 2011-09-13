/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.ucr");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.ExpandingTitlePane");

dojo.declare("umc.modules.ucr", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,
	_page: null,

	moduleID: 'ucr',
	idProperty: 'key',

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		// generate border layout and add it to the module
		this._page = new umc.widgets.Page({
			headerText: this._('Univention Config Registry'),
			helpText: this._('The Univention Config Registry (UCR) is the central tool that allows to access and edit system-wide properties in a unified manner. These settings can be settings such as a static IP address, DNS forwarders, proxies, hostname etc. When changes are made to UCR variables, depending system configuration files are updated.')
		});
		this.addChild(this._page);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Entries')
		});
		this._page.addChild(titlePane);

		//
		// add data grid
		//

		// define actions
		var actions = [{
			name: 'add',
			label: this._( 'Add' ),
			description: this._( 'Adding a new UCR variable' ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				this._detailDialog.newVariable();
			})
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Setting the UCR variable, editing the categories and/or description' ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids) {
				if (ids.length) {
					this._detailDialog.loadVariable(ids[0]);
				}
			})
		}, {
			name: 'delete',
			label: this._( 'Delete' ),
			description: this._( 'Deleting the selected UCR variables' ),
			iconClass: 'dijitIconDelete',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function(ids) {
				var transaction = this.moduleStore.transaction();
				dojo.forEach(ids, dojo.hitch(this.moduleStore, 'remove'));
				transaction.commit();
			})
		}];

		// define grid columns
		var columns = [{
			name: 'key',
			label: this._( 'UCR variable' ),
			description: this._( 'Unique name of the UCR variable' ),
			editable: false
		}, {
			name: 'value',
			label: this._( 'Value' ),
			description: this._( 'Value of the UCR variable' ),
			editable: true
		}];

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
				category: "all",
				key: "all",
				filter:"*"
			}
		});
		titlePane.addChild(this._grid);

		//
		// add search widget
		//

		// define the different search widgets
		var widgets = [{
			type: 'ComboBox',
			name: 'category',
			value: 'all',
			description: this._( 'Category the UCR variable should associated with' ),
			label: this._('Category'),
			staticValues: [
				{ id: 'all', label: this._('All') }
			],
			dynamicValues: 'ucr/categories'
		}, {
			type: 'ComboBox',
			name: 'key',
			value: 'all',
			description: this._( 'Select the attribute of a UCR variable that should be search for the given keyword' ),
			label: this._( 'Search attribute' ),
			staticValues: [
				{ id: 'all', label: this._( 'All' ) },
				{ id: 'key', label: this._( 'Variable' ) },
				{ id: 'value', label: this._( 'Value' ) },
				{ id: 'description', label: this._( 'Description' ) }
			]
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			description: this._( 'Keyword that should be searched for in the selected attribute' ),
			label: this._( 'Keyword' )
		}];

		// generate the search widget
		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [[ 'category', 'key' ], [ 'filter', 'submit', 'reset' ]],
			onSearch: dojo.hitch(this._grid, 'filter')
		});
		titlePane.addChild(this._searchWidget);

		this._page.startup();

		//
		// create dialog for UCR variable details
		//

		this._detailDialog = new umc.modules.ucr._DetailDialog({
			moduleStore: this.moduleStore
		});
		this._detailDialog.startup();
	}

});

dojo.declare("umc.modules.ucr._DetailDialog", [ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	_form: null,

	// use i18n information from umc.modules.ucr
	i18nClass: 'umc.modules.ucr',

	moduleStore: null,

	postMixInProperties: function() {
		// call superclass method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: this._( 'Edit UCR variable' )
			//style: 'max-width: 450px'
		});
	},

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'key',
			description: this._( 'Name of UCR variable' ),
			label: this._( 'UCR variable' )
		}, {
			type: 'TextBox',
			name: 'value',
			description: this._( 'Value of UCR variable' ),
			label: this._( 'Value' )
//		}, {
//			type: 'MultiSelect',
//			name: 'categories',
//			description: this._( 'Categories that the UCR variable is assoziated with' ),
//			label: this._( 'Categories' ),
//			dynamicValues: 'ucr/categories'
		}];

		var buttons = [{
			name: 'submit',
			label: this._( 'Save' ),
			callback: dojo.hitch(this, function() {
				this._form.save();
				this.hide();
			})
		}, {
			//FIXME: Should be much simpled. The key name should be enough
			name: 'cancel',
			label: this._( 'Cancel' ),
			callback: dojo.hitch(this, function() {
				this.hide();
			})
		}];

		var layout = [['key'], ['value']];//, ['categories']];

		this._form = new umc.widgets.Form({
			style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			moduleStore: this.moduleStore,
			cols: 1
		}).placeAt(this.containerNode);

		// simple handler to disable standby mode
		dojo.connect(this._form, 'onLoaded', this, function() {
			this.standby(false);
		});
		dojo.connect(this._form, 'onSaved', this, function() {
			this.standby(false);
		});

	},

	clearForm: function() {
		var emptyValues = {};
		umc.tools.forIn(this._form.gatherFormValues(), function(ikey) {
			emptyValues[ikey] = '';
		});
		this._form.setFormValues(emptyValues);
	},

	newVariable: function() {
		this._form._widgets.key.set('disabled', false);
		this.clearForm();
		this.standby(false);
		this.show();
	},

	loadVariable: function(ucrVariable) {
		this._form._widgets.key.set('disabled', true);

		// start standing-by mode
		this.standby(true);
		this.show();

		// clear form and start the query
		this.clearForm();
		this._form.load(ucrVariable);
	},

	getValues: function() {
		// description:
		//		Collect a property map of all currently entered/selected values.

		return this._form.gatherFormValues();
	},

	onSubmit: function(values) {
		// stub for event handling
	}
});


