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
dojo.require("umc.modules._uvmm.DomainPage");

dojo.declare("umc.modules.uvmm", [ umc.widgets.Module, umc.i18n.Mixin ], {

	// the property field that acts as unique identifier
	idProperty: 'id',

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the detail page for editing an UDM object
	_domainPage: null,

	// reference to a `umc.widgets.Tree` instance which is used to display the container
	// hierarchy for the UDM navigation module
	_tree: null,

	// reference to the last item in the navigation on which a context menu has been opened
	_navContextItem: null,

	_progressBar: null,
	_progressContainer: null,

	uninitialize: function() {
		this.inherited(arguments);

		this._progressContainer.destroyRecursive();
	},

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
		// STATES = ( 'NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED' )
		var actions = [{
			name: 'edit',
			label: this._('Configure'),
			isStandardAction: true,
			isMultiAction: false,
			iconClass: 'umcIconEdit',
			callback: dojo.hitch(this, 'openDomainPage')
		}, {
			name: 'start',
			label: this._('Start'),
			iconClass: 'umcIconPlay',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, 'changeState', 'RUN'),
			canExecute: function(item) {
				return item.state != 'RUNNING' && item.state != 'IDLE';
			}
		}, {
			name: 'stop',
			label: this._( 'Stop' ),
			iconClass: 'umcIconStop',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, 'changeState', 'SHUTDOWN'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, {
			name: 'pause',
			label: this._('Pause'),
			iconClass: 'umcIconPause',
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, 'changeState', 'PAUSE'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, {
			name: 'restart',
			label: this._( 'Restart' ),
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, 'changeState', 'RESTART'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}];

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
			iconClass: 'umcIconEdit',
			onClick: dojo.hitch(this, function(e) {
				this.createDomainPage(this._navContextItem.objectType, this._navContextItem.id);
			})
		}));
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Delete' ),
			iconClass: 'umcIconDelete',
			onClick: dojo.hitch(this, function() {
				this.removeObjects(this._navContextItem.id);
			})
		}));
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Reload' ),
			iconClass: 'umcIconRefresh',
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

		// setup a progress bar with some info text
		this._progressContainer = new umc.widgets.ContainerWidget({});
		this._progressBar = new dijit.ProgressBar({
			style: 'background-color: #fff;'
		});
		this._progressContainer.addChild(this._progressBar);
		this._progressContainer.addChild(new umc.widgets.Text({
			content: this._('Please wait, your requests are being processed...')
		}));

		// setup the detail page
		this._domainPage = new umc.modules._uvmm.DomainPage({
			onClose: dojo.hitch(this, function() {
				this.selectChild(this._searchPage);
			})
		});
		this.addChild(this._domainPage);

		// register events
		this.connect(this._domainPage, 'onUpdateProgress', 'updateProgress');
	},

	postCreate: function() {
		this.inherited(arguments);

		this._tree.watch('path', dojo.hitch(this, function() {
			var searchType = this._searchForm.getWidget('type').get('value');
			if (searchType == 'domain') {
				this.filter();
			}
		}));
	},

	openDomainPage: function(ids) {
		if (!ids.length) {
			return;
		}
		this._domainPage.load(ids[0]);
		this.selectChild(this._domainPage);
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
		else if (item.type == 'domain') {
			if (item.state == 'RUNNING' || item.state == 'IDLE') {
				iconName += '-on';
			}
			else if (item.state == 'PAUSED') {
				iconName += '-paused';
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

	changeState: function(/*String*/ newState, ids) {
		// chain all UMCP commands
		var deferred = new dojo.Deferred();
		deferred.resolve();
		dojo.forEach(ids, function(iid, i) {
			deferred = deferred.then(dojo.hitch(this, function() {
				this.updateProgress(i, ids.length);
				return umc.tools.umcpCommand('uvmm/domain/state', {
					domainURI: iid,
					domainState: newState
				}); 
			}));
		}, this);

		// finish the progress bar and add error handler
		deferred = deferred.then(dojo.hitch(this, function() {
			this.moduleStore.onChange();
			this.updateProgress(ids.length, ids.length);
		}), dojo.hitch(this, function() {
			umc.dialog.alert(this._('An error ocurred during processing your request.'));
			this.moduleStore.onChange();
			this.updateProgress(ids.length, ids.length);
		}));
	},

	updateProgress: function(i, n) {
		var progress = this._progressBar;
		if (i === 0) {
			// initiate the progressbar and start the standby
			progress.set('maximum', n);
			progress.set('value', 0);
			this.standby(true, this._progressContainer);
		}
		else if (i >= n || i < 0) {
			// finish the progress bar
			progress.set('value', n);
			this.standby(false);
		}
		else {
			progress.set('value', i);
		}
	}
});



