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

dojo.provide("umc.modules.ucr");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules.ucr", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchForm: null,
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
			headerText: this._('Univention Configuration Registry'),
			helpText: this._('The Univention Configuration Registry (UCR) is the local database for the configuration of UCS systems to access and edit system-wide properties in a unified manner. Caution: Changing UCR variables directly results in the change of the system configuration. Misconfiguration may cause an usable system!')
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
			iconClass: 'umcIconAdd',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				this._detailDialog.newVariable();
			})
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Setting the UCR variable, editing the categories and/or description' ),
			iconClass: 'umcIconEdit',
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
			iconClass: 'umcIconDelete',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function(ids) {
				umc.dialog.confirm(this._('Are you sure to delete the %d select UCR variable(s)?', ids.length), [{
					label: this._('Delete'),
					callback: dojo.hitch(this, function() {
						// remove the selected elements via a transaction on the module store
						var transaction = this.moduleStore.transaction();
						dojo.forEach(ids, dojo.hitch(this.moduleStore, 'remove'));
						transaction.commit();
					})
				}, {
					label: this._('Cancel'),
					'default': true
				}]);

			})
		}];

		// define grid columns
		var columns = [{
			name: 'key',
			label: this._( 'UCR variable' ),
			description: this._( 'Unique name of the UCR variable' )
		}, {
			name: 'value',
			label: this._( 'Value' ),
			description: this._( 'Value of the UCR variable' )
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
			description: this._( 'Category the UCR variable should be associated with' ),
			label: this._('Category'),
			staticValues: [
				{ id: 'all', label: this._('All') }
			],
			dynamicValues: 'ucr/categories',
			size: 'TwoThirds'
		}, {
			type: 'ComboBox',
			name: 'key',
			value: 'all',
			description: this._( 'Select the attribute of a UCR variable that should be searched for the given keyword' ),
			label: this._( 'Search attribute' ),
			staticValues: [
				{ id: 'all', label: this._( 'All' ) },
				{ id: 'key', label: this._( 'Variable' ) },
				{ id: 'value', label: this._( 'Value' ) },
				{ id: 'description', label: this._( 'Description' ) }
			],
			size: 'TwoThirds'
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			description: this._( 'Keyword that should be searched for in the selected attribute' ),
			label: this._( 'Keyword' ),
			size: 'TwoThirds'
		}];

		// generate the search widget
		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [[ 'category', 'key', 'filter', 'submit' ]],
			onSearch: dojo.hitch(this._grid, 'filter')
		});
		titlePane.addChild(this._searchForm);

		this._page.startup();

		// make sure that the input field is focused
		this.connect(this, 'onShow', '_selectInputText');
		this.connect(this._grid, 'onFilterDone', '_selectInputText');

		//
		// create dialog for UCR variable details
		//

		this._detailDialog = new umc.modules.ucr._DetailDialog({
			moduleStore: this.moduleStore
		});
		this._detailDialog.startup();
	},

	_selectInputText: function() {
		// focus on input widget
		var widget = this._searchForm.getWidget('filter');
		widget.focus();

		// select the text
		if (widget.textbox) {
			dijit.selectInputText(widget.textbox);
		}
	}
});

dojo.declare("umc.modules.ucr._DetailDialog", [ dijit.Dialog, umc.widgets.StandbyMixin, umc.widgets._WidgetsInWidgetsMixin, umc.i18n.Mixin ], {
	_form: null,

	_description: null,

	// use i18n information from umc.modules.ucr
	i18nClass: 'umc.modules.ucr',

	moduleStore: null,

	postMixInProperties: function() {
		// call superclass method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: this._( 'Edit UCR variable' ),
			style: 'max-width: 400px'
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
			description: this._( 'Value of the UCR variable' ),
			label: this._( 'Value' )
		}, {
			type: 'Text',
			name: 'description',
			description: this._( 'Description of the UCR variable' ),
			label: this._( 'Description:' )
		}, {
			type: 'HiddenInput',
			name: 'description[' + dojo.locale + ']'
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

		var layout = ['key', 'value', 'description'];//, ['categories']];

		this._form = this.adopt(umc.widgets.Form, {
			style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			moduleStore: this.moduleStore,
			cols: 1
		});
		this._form.placeAt(this.containerNode);

		// simple handler to disable standby mode
		this.connect(this._form, 'onLoaded', function() {
			// display the description text
			var descWidget = this._form.getWidget('description');
			var text = this._form.getWidget('description[' + dojo.locale + ']').get('value');
			if (text) {
				// we have description, update the description field
				descWidget.set('visible', true);
				descWidget.set('content', '<i>' + text + '</i>');
			}
			else {
				// no description -> hide widget and label
				descWidget.set('visible', false);
				descWidget.set('content', '');
			}

			// disable the loading animation
			this._position();
			this.standby(false);
		});
		this.connect(this._form, 'onSaved', function() {
			this._position();
			this.standby(false);
		});

	},

	clearForm: function() {
		var emptyValues = {};
		umc.tools.forIn(this._form.gatherFormValues(), function(ikey) {
			emptyValues[ikey] = '';
		});
		this._form.setFormValues(emptyValues);
		var descWidget = this._form.getWidget('description');
		descWidget.set('content', '');
		descWidget.set('visible', false);
		this._position();
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


