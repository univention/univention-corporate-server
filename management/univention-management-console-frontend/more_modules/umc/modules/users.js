/*
 * Copyright 2011-2012 Univention GmbH
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

dojo.provide("umc.modules.users");

dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.Module");
dojo.require("umc.tools");
dojo.require("dojo.data.ItemFileReadStore");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojox.grid.EnhancedGrid");
//dojo.require("dojox.grid.DataGrid");
dojo.require("dojox.grid.enhanced.plugins.Menu");
dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");
dojo.require("dojox.grid.cells");
dojo.require("dojox.layout.TableContainer");
dojo.require("dijit.Dialog");
dojo.require("dijit.Menu");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.form.Textarea");
dojo.require("dijit.form.ComboBox");
dojo.require("dijit.form.CheckBox");
dojo.require("dojox.form.CheckedMultiSelect");
dojo.require("dojox.widget.Standby");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.ComboBox");

dojo.declare("umc.modules._usersUser", umc.widgets.TabbedModule, {
	postMixInProperties: function() {
		// call superclass' method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: 'Edit User',
			iconClass: 'icon16-users',
			closable: true
		});
	},

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		// embed layout container within a form-element
		this._form = new umc.widgets.ContainerForm({
			region: 'center',
			onSubmit: dojo.hitch(this, function(evt) {
				//dojo.stopEvent(evt);
				//this.onSubmit(this.getValues());
			})
		});
		// create some dummy tabs
		/*var tabContainer = new dijit.layout.TabContainer({
			region: 'center',
			tabPosition: 'right-h'
		}).placeAt(this.containerNode);*/

		this._form.addChild(new dijit.layout.ContentPane({
			content: '<h1>Grundeinstellungen</h1><p>Auf dieser Seite können Sie die Grundeinstellungen eines Benutzers bearbeiten. Ueber die Reiter der rechten Seite können sie spezifischere Einstellungen zu dem Benutzer vornehmen.</p>'
		}));

		// create a table container which contains all search elements
		this._container = new dojox.layout.TableContainer({
			cols: 2,
			showLabels: true,
			orientation: 'vert'
		});
		this._form.addChild(this._container);

		// TextBoxes
		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Benutzername',
			value: ''
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Beschreibung',
			value: ''
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Passwort',
			value: ''
		}));

		this._container.addChild(new dijit.form.CheckBox({
			//style: 'width: 90%',
			label: 'Passwort-History ignorieren',
			checked: false
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Passwort (Wiederholung)',
			value: ''
		}));

		this._container.addChild(new dijit.form.CheckBox({
			//style: 'width: 90%',
			label: 'Passwort-Prüfungen ignorieren',
			checked: false
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Vorname',
			value: ''
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Nachname',
			value: ''
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Title',
			value: ''
		}));

		this._container.addChild(new dijit.form.TextBox({
			style: 'width: 90%',
			label: 'Organisation',
			value: ''
		}));

		// add 'ok' button
		var buttonContainer = new umc.widgets.ContainerWidget({
			colspan: 2,
			style: 'text-align: right; width: 90%'
		});
		this._container.addChild(buttonContainer);
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Ok',
			//type: 'submit',
			'class': 'submitButton'
		}));
	
		// add 'cancel' button
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Abbrechen',
			onClick: dojo.hitch(this, function() {
				this.destroyRecursively();
			})
		}));
		
		// create tabs
		this.addTab('Allgemein', this._form);
		this.addTab('Benutzer-Konto', '');
		this.addTab('Mail', '');
		this.addTab('Kontakt', '');
		this.addTab('Organisation', '');
		this.addTab('Kontakt privat', '');
		this.addTab('(Optionen)', '');
	}
});

dojo.declare("umc.modules.users", umc.widgets.Module, {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,
	_categoryStore: new dojo.data.ItemFileWriteStore({
		//url: 'json/ucr_categories.json'
		data: { 
			identifier: 'id',
			label: 'name',
			items: [{
				id: 'all',
				name: 'All'
			}]
		} 
	}),

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		// add search widget
		this._searchWidget = new umc.widgets.SearchForm({
			fields: [
				{
					id: 'searchin',
					label: 'Suchen in',
					//value: 'id1',
					labelAttr: 'text',
					store: new dojo.data.ItemFileReadStore({ data: {
						identifier: 'id',
						label: 'text',
						items: [
							{ id: 'id1', text: 'Alle registrierten Benutzer-Container' },
							{ id: 'id2', text: 'Nur univention.qa:/users/' },
							{ id: 'id3', text: 'Ausgewählte Domäne' },
							{ id: 'id4', text: 'Ausgewählte Domäne und deren Unterdomänen' }
						]
					}})
				},
				null,
				{
					id: 'mask',
					label: 'Eigenschaft',
					labelAttr: 'text',
					store: new dojo.data.ItemFileReadStore({ data: {
						identifier: 'id',
						label: 'text',
						items: [
							{ id: 'id1', text: 'Alle' },
							{ id: 'id2', text: 'Benutzername' },
							{ id: 'id3', text: 'Nachname' },
							{ id: 'id4', text: 'Vorname' }
						]
					}})
				},
				{
					id: 'search',
					label: 'Suche',
					value: '*'
				}
			]
			//onSubmit: dojo.hitch(this, this.filter)
		});
		this.addChild(this._searchWidget);

		//
		// create toolbar
		//

		// first create a container for grid and tool bar
		//var gridContainer = new dijit.layout.BorderContainer({
		//	region: 'center'
		//});
		//this.addChild(gridContainer);

		// create the toolbar container
		var toolBar = new umc.widgets.ContainerWidget({
			region: 'bottom',
			style: 'text-align: right'
		});
		this.addChild(toolBar);

		// create 'report' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Report erstellen',
			iconClass: 'dijitIconFile',
			onClick: dojo.hitch(this, function() {
				/*var vars = this.getSelectedVariables();
				if (vars.length) {
					this._detailDialog.loadVariable(vars[0]);
				}*/
			})
		}));

		// create 'edit' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Edit',
			iconClass: 'dijitIconEdit',
			onClick: dojo.hitch(this, function() {
				this.openUserTab();
				/*var vars = this.getSelectedVariables();
				if (vars.length) {
					this._detailDialog.loadVariable(vars[0]);
				}*/
			})
		}));

		// create 'add' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Add',
			iconClass: 'dijitIconNewTask',
			onClick: dojo.hitch(this, function() {
				this.openUserTab();
				//this._detailDialog.newVariable();
			})
		}));

		// create 'delete' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Delete',
			iconClass: 'dijitIconDelete',
			onClick: dojo.hitch(this, function() {
				/*var vars = this.getSelectedVariables();
				if (vars.length) {
					this.unsetVariable(vars[0]);
				}*/
			})
		}));

		//
		// create menus for grid
		//

		// menu for selected entries
		this._selectMenuItems = {};
		dojo.mixin(this._selectMenuItems, {
			edit: new dijit.MenuItem({
				label: 'Edit',
				iconClass: 'dijitIconEdit',
				onClick: dojo.hitch(this, function() {
					this.openUserTab();
					/*console.log('### onClick');
					console.log(arguments);
					var vars = this.getSelectedVariables();
					if (vars.length) {
						this._detailDialog.loadVariable(vars[0]);
					}*/
				})
			}),
			del: new dijit.MenuItem({
				label: 'Delete',
				iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, function() {
					/*var vars = this.getSelectedVariables();
					if (vars.length) {
						this.unsetVariable(vars[0]);
					}*/
				})
			}),
			add: new dijit.MenuItem({
				label: 'Add',
				iconClass: 'dijitIconNewTask',
				onClick: dojo.hitch(this, function() {
					this.openUserTab();
					//this._detailDialog.newVariable();
				})
			})
		});
	
		// put menu items together
		this._selectMenu = new dijit.Menu({ });
		this._selectMenu.addChild(this._selectMenuItems.edit);
		this._selectMenu.addChild(this._selectMenuItems.del);
		this._selectMenu.addChild(this._selectMenuItems.add);

		// menu for cells
		this._cellMenuItems = {};
		dojo.mixin(this._cellMenuItems, {
			edit: new dijit.MenuItem({
				label: 'Edit',
				iconClass: 'dijitIconEdit',
				onClick: dojo.hitch(this, function() {
					this.openUserTab();
					/*if (this._contextVariable) {
						this._detailDialog.loadVariable(this._contextVariable);
					}*/
				})
			}),
			del: new dijit.MenuItem({
				label: 'Delete',
				iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, function() {
					this.openUserTab();
					/*if (this._contextVariable) {
						this.unsetVariable(this._contextVariable);
					}*/
				})
			}),
			add: new dijit.MenuItem({
				label: 'Add',
				iconClass: 'dijitIconNewTask',
				onClick: dojo.hitch(this, function() {
					this.openUserTab();
					//this._detailDialog.newVariable();
				})
			})
		});

		// put menu items together
		this._cellMenu = new dijit.Menu({ });
		this._cellMenu.addChild(this._cellMenuItems.edit);
		this._cellMenu.addChild(this._cellMenuItems.del);
		this._cellMenu.addChild(this._cellMenuItems.add);

		//
		// create the grid
		//

		// create store
		this._store = new dojo.data.ItemFileWriteStore({ data: {items:[]} });
		var layout = [{
			field: 'object',
			name: 'Objekt',
			width: 'auto'
		},{
			field: 'path',
			name: 'Ort',
			width: 'auto',
			editable: true
		}];
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			region: 'center',
			query: { object: '*', path: '*' },
			queryOptions: { ignoreCase: true },
			structure: layout,
			clientSort: true,
			store: new dojo.data.ItemFileReadStore({ data: {
				identifier: 'id',
				label: 'object',
				items: [
					{ id: 'id1', object: 'Administrator', path: 'univention.qa:/users/' },
					{ id: 'id2', object: 'join-backup', path: 'univention.qa:/users/' },
					{ id: 'id3', object: 'join-slave', path: 'univention.qa:/users/' },
					{ id: 'id4', object: 'spam', path: 'univention.qa:/users/' }
				]
			}}),
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

		//// disable edit menu in case there is more than one item selected
		//dojo.connect(this._grid, 'onSelectionChanged', dojo.hitch(this, function() {
		//	var nItems = this._grid.selection.getSelectedCount();
		//	this._selectMenuItems.edit.set('disabled', nItems > 1);
		//}));

		//// save internally for which row the cell context menu was opened
		//dojo.connect(this._grid, 'onCellContextMenu', dojo.hitch(this, function(e) {
		//	var item = this._grid.getItem(e.rowIndex);
		//	this._contextVariable = this._store.getValue(item, 'key');
		//}));

		//// connect to row edits
		//dojo.connect(this._grid, 'onApplyEdit', this, function(rowIndex) {
		//	// get the ucr variable and value of edited row
		//	var item = this._grid.getItem(rowIndex);
		//	var ucrVar = this._store.getValue(item, 'key');
		//	var ucrVal = this._store.getValue(item, 'value');
		//	
		//	// while saving, set module to standby
		//	this.standby(true);

		//	// save values
		//	this.saveVariable(ucrVar, ucrVal, dojo.hitch(this, function() {
		//		this.standby(false);
		//	}), false);
		//});

		//// create dialog for UCR variable details
		//this._detailDialog = new umc.modules._ucrDetailDialog({});
		//this._detailDialog.startup();

		//
		// query categories from server 
		//

	},

	openUserTab: function() {
		var tab = new umc.modules._usersUser({});
		umc.app._tabContainer.addChild(tab);
		umc.app._tabContainer.selectChild(tab, true);
	}

//	getSelectedVariables: function() {
//		var items = this._grid.selection.getSelected();
//		var vars = [];
//		for (var iitem = 0; iitem < items.length; ++iitem) {
//			vars.push(this._store.getValue(items[iitem], 'key'));
//		}
//		console.log('### getSelectedVariables');
//		console.log(vars);
//		console.log(items);
//		return vars;
//	}

});


