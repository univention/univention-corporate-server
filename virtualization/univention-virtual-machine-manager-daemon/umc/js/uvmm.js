/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.uvmm");

dojo.require("dijit.Menu");
dojo.require("dijit.MenuItem");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.ProgressBar");
dojo.require("dojo.DeferredList");
dojo.require("dojox.string.sprintf");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Tree");

//dojo.require("umc.modules._udm.Template");
//dojo.require("umc.modules._udm.NewObjectDialog");
dojo.require("umc.modules._uvmm.TreeModel");
//dojo.require("umc.modules._udm.DetailPage");

dojo.declare("umc.modules.uvmm", [ umc.widgets.Module, umc.i18n.Mixin ], {

	// the property field that acts as unique identifier
	idProperty: 'id',

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the detail page for editing an UDM object
	_detailPage: null,

	// reference to a `umc.widgets.Tree` instance which is used to display the container
	// hierarchy for the UDM navigation module
	_tree: null,

	// reference to the last item in the navigation on which a context menu has been opened
	_navContextItem: null,

	postMixInProperties: function() {
		this.inherited(arguments);
	},

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		// setup search page
		this._searchPage = new umc.widgets.Page({
			headerText: 'Univention Virtual Machine Manager'
		});
		this.addChild(this._searchPage);
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Search for virtual machines and virtualization servers'),
			design: 'sidebar'
		});
		this._searchPage.addChild(titlePane);

		//
		// add data grid
		//

		// define actions
		var actions = [/*{
			name: 'add',
			label: this._( 'Add %s', this.objectNameSingular ),
			description: this._( 'Add a new %s.', this.objectNameSingular ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, 'showNewObjectDialog')
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Edit the %s.', this.objectNameSingular ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids, items) {
				if (items.length && items[0].objectType) {
					this.createDetailPage(items[0].objectType, ids[0]);
				}
			})
		}, {
			name: 'editNewTab',
			label: this._('Edit in new tab'),
			description: this._( 'Open a new tab in order to edit the UDM-object' ),
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids, items) {
				var moduleProps = {
					openObject: {
						objectType: items[0].objectType,
						objectDN: ids[0]
					}
				};
				dojo.publish('/umc/modules/open', [ this.moduleID, this.moduleFlavor, moduleProps ]);
			})
		}, {
			name: 'delete',
			label: this._( 'Delete' ),
			description: this._( 'Deleting the selected %s.', this.objectNamePlural ),
			isStandardAction: true,
			isMultiAction: true,
			iconClass: 'dijitIconDelete',
			callback: dojo.hitch(this, function(ids) {
				if (ids.length) {
					this.removeObjects(ids);
				}
			})
		}*/];

		// search widgets
		var widgets = [{
			type: 'ComboBox',
			name: 'type',
			label: this._('Displayed type'),
			staticValues: [
				{ id: 'domain', label: this._('Virtual machine') },
				{ id: 'node', label: this._('Virtualization sever') }
			],
			size: 'Half' 
		}, {
			type: 'TextBox',
			name: 'pattern',
			label: 'Query pattern',
			size: 'One',
			value: '*'
		}];
		var layout = [[ 'type', 'pattern', 'submit' ]];

		// generate the search widget
		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: layout,
			onSearch: dojo.hitch(this, 'filter')
		});
		titlePane.addChild(this._searchForm);

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: this._getGridColumns('domain'),
			moduleStore: this.moduleStore
			/*footerFormatter: dojo.hitch(this, function(nItems, nItemsTotal) {
				// generate the caption for the grid footer
				if (0 === nItemsTotal) {
					return this._('No %(objPlural)s could be found', map);
				}
				else if (1 == nItems) {
					return this._('%(nSelected)d %(objSingular)s of %(nTotal)d selected', map);
				}
				else {
					return this._('%(nSelected)d %(objPlural)s of %(nTotal)d selected', map);
				}
			}),*/
		});

		titlePane.addChild(this._grid);
		// generate the navigation tree
		var model = new umc.modules._uvmm.TreeModel({
			umcpCommand: dojo.hitch(this, 'umcpCommand')
		});
		this._tree = new umc.widgets.Tree({
			//style: 'width: auto; height: auto;',
			model: model,
			persist: false,
			showRoot: false,
			autoExpand: true,
			path: [ model.root.id, 'default' ],
			// customize the method getIconClass()
			//onClick: dojo.hitch(this, 'filter'),
			getIconClass: dojo.hitch(this, function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
				return umc.tools.getIconClass(this._iconClass(item));
			})
		});
		var treePane = new dijit.layout.ContentPane({
			content: this._tree,
			region: 'left',
			splitter: true,
			style: 'width: 200px;'
		});
		titlePane.addChild(treePane);

		// add a context menu to edit/delete items
		/*
		var menu = dijit.Menu({});
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Edit' ),
			iconClass: 'dijitIconEdit',
			onClick: dojo.hitch(this, function(e) {
				this.createDetailPage(this._navContextItem.objectType, this._navContextItem.id);
			})
		}));
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Delete' ),
			iconClass: 'dijitIconDelete',
			onClick: dojo.hitch(this, function() {
				this.removeObjects(this._navContextItem.id);
			})
		}));
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Reload' ),
			iconClass: 'dijitIconUndo',
			onClick: dojo.hitch(this, function() {
				this._tree.reload();
			})
		}));*/

		// when we right-click anywhere on the tree, make sure we open the menu
		//menu.bindDomNode(this._tree.domNode);

		// remember on which item the context menu has been opened
		/*this.connect(menu, '_openMyself', function(e) {
			var el = dijit.getEnclosingWidget(e.target);
			if (el) {
				this._navContextItem = el.item;
			}
		});*/

		this._searchPage.startup();
	},

	postCreate: function() {
		this.inherited(arguments);

		this._tree.watch('path', dojo.hitch(this, function() {
			this.filter();
		}))
	},

	_getGridColumns: function(type) {
		if (type == 'node') {
			return [{
				name: 'label',
				label: this._('Name'),
				formatter: dojo.hitch(this, 'iconFormatter')
			}, {
				name: 'cpuUsage',
				label: this._('CPU usage'),
				formatter: dojo.hitch(this, 'cpuUsageFormatter')
			}, {
				name: 'memUsed',
				label: this._('Memory usage'),
				formatter: dojo.hitch(this, 'memoryUsageFormatter')
			}];
		}

		// else type == 'domain'
		return [{
			name: 'label',
			label: this._('Name'),
			formatter: dojo.hitch(this, 'iconFormatter')
		}, {
			name: 'cpuUsage',
			label: this._('CPU usage'),
			formatter: dojo.hitch(this, 'cpuUsageFormatter')
		}, {
			name: 'mem',
			label: this._('Memory available'),
			formatter: dojo.hitch(this, 'memoryUsageFormatter')
		}];
	},

	cpuUsageFormatter: function(id, rowIndex) {
		// summary:
		//		Formatter method for cpu usage.

		var item = this._grid._grid.getItem(rowIndex);
		var percentage = Math.round(item.cpuUsage);
		return new dijit.ProgressBar({
			value: percentage + '%'
		});
	},

	memoryUsageFormatter: function(id, rowIndex) {
		// summary:
		//		Formatter method for cpu usage.

		var item = this._grid._grid.getItem(rowIndex);
		if (item.type == 'node') {
			// for the node, return a progressbar
			var percentage = Math.round(item.cpuUsage);
			return new dijit.ProgressBar({
				label: dojox.string.sprintf('%.1f GB / %.1f GB', item.memUsed / 1073741824.0, item.memAvailable / 1073741824.0),
				maximum: item.memAvailable,
				value: item.memUsed
			});
		}
		
		// else: item.type == 'domain'
		// for the domain, return a simple string
		return dojox.string.sprintf('%.1f GB', (item.mem || 0) / 1073741824.0);
	},

	_iconClass: function(item) {
		var iconName = 'uvmm-' + item.type;
		if (item.type == 'node') {
			if (item.virtech) {
				iconName += '-' + item.virtech;
			}
			if (!item.available) {
				iconName += '-off';	
			}
		}
		return iconName;
	},

	iconFormatter: function(label, rowIndex) {
		// summary:
		//		Formatter method that adds in a given column of the search grid icons
		//		according to the object types.

		// create an HTML image that contains the icon (if we have a valid iconName)
		var item = this._grid._grid.getItem(rowIndex);
		return dojo.string.substitute('<img src="images/icons/16x16/${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${label}', {
			icon: this._iconClass(item),
			height: '16px',
			width: '16px',
			label: label
		});
	},

	filter: function() {
		// summary:
		//		Send a new query with the given filter options as specified in the search form
		//		and the selected server/group.

		// validate the search form
		var _vals = this._searchForm.gatherFormValues();
		_vals.pattern = _vals.pattern === '' ? '*' : _vals.pattern;
		if (!this._searchForm.getWidget('type').isValid()) {
			umc.dialog.alert(this._('Please select a valid search type.'));
			return;
		}
		
		var path = this._tree.get('path');
		var treeType = 'root';
		var treeID = '';
		if (path.length) {
			var item = path[path.length - 1];
			treeType = item.type || 'node';
			treeID = item.id;
		}

		// build the query we need to send to the server
		var vals = { 
			type: _vals.type,
			domainPattern: '*',
			nodePattern: '*'
		};
		if (vals.type == 'domain') {
			vals.domainPattern = _vals.pattern;
		}
		else {
			vals.nodePattern = _vals.pattern;
		}
		if (treeType == 'node' && vals.type == 'domain') {
			// search for domains only in the scope of the given node
			vals.nodePattern = treeID;
		}

		this._grid.filter(vals);

		// update the grid columns
		this._grid.set('columns', this._getGridColumns(vals.type));
	},

	removeObjects: function(/*String|String[]*/ _ids) {
		// summary:
		//		Remove the selected UDM objects.

		// get an array
		var ids = dojo.isArray(_ids) ? _ids : (_ids ? [ _ids ] : []);

		// ignore empty array
		if (!ids.length) {
			return;
		}

		// let user confirm deletion
		var msg = this._('Please confirm the removal of the %d selected %s!', ids.length, this.objectNamePlural);
		if (ids.length == 1) {
			msg = this._('Please confirm the removal of the selected %s!', this.objectNameSingular);
		}
		umc.dialog.confirm(msg, [{
			label: this._('Delete'),
			callback: dojo.hitch(this, function() {
				// remove the selected elements via a transaction on the module store
				var transaction = this.moduleStore.transaction();
				dojo.forEach(ids, function(iid) {
					this.moduleStore.remove(iid);
				}, this);
				transaction.commit();
			})
		}, {
			label: this._('Cancel')
		}]);

	}

});



