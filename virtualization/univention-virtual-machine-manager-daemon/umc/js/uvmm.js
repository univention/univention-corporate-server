/*global window console MyError dojo dojox dijit umc */

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
dojo.require("umc.modules._uvmm.DomainWizard");

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

	_finishedDeferred: null,
	_ucr: null,

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

		// load asynchronously some UCR variables
		this._finishedDeferred = new dojo.Deferred();
		umc.tools.ucr('uvmm/umc/*').then(dojo.hitch(this, function(ucr) {
			this._ucr = ucr;
			this._finishedDeferred.resolve(this._ucr);
		}));

		// setup search page
		this._searchPage = new umc.widgets.Page({
			headerText: 'Univention Virtual Machine Manager'
			//helpText: this._('<p>This module provides a management interface for physical servers that are registered within the UCS domain.</p><p>The tree view on the left side shows an overview of all existing physical servers and the residing virtual instances. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual instance can be invoked on each of the instances.</p><p>Also possible is direct access to virtual instances. Therefor it must be activated in the configuration.</p><p>Each virtual instance entry in the tree view provides access to detailed information und gives the possibility to change the configuration or state and migrated it to another physical server.</p>')
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
		var types = umc.modules._uvmm.types;
		var actions = [{
			name: 'edit',
			label: this._( 'Edit' ),
			isStandardAction: true,
			isMultiAction: false,
			iconClass: 'umcIconEdit',
			description: this._( 'Edit the configuration of the virtual instance' ),
			callback: dojo.hitch(this, 'openDomainPage')
		}, {
			name: 'start',
			label: this._( 'Start' ),
			iconClass: 'umcIconPlay',
			description: this._( 'Start the virtual instance' ),
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, '_changeState', 'RUN'),
			canExecute: function(item) {
				return item.state != 'RUNNING' && item.state != 'IDLE';
			}
		}, {
			name: 'stop',
			label: this._( 'Stop' ),
			iconClass: 'umcIconStop',
			description: this._( 'Shut off the virtual instance' ),
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, '_changeState', 'SHUTDOWN'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, {
			name: 'pause',
			label: this._( 'Pause' ),
			iconClass: 'umcIconPause',
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, '_changeState', 'PAUSE'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, {
 			name: 'suspend',
 			label: this._( 'Save & Stop' ),
 			// iconClass: 'umcIconPause',
 			isStandardAction: false,
 			isMultiAction: true,
 			callback: dojo.hitch(this, '_changeState', 'SUSPEND'),
 			canExecute: function(item) {
 				return ( item.state == 'RUNNING' || item.state == 'IDLE' ) && types.getNodeType( item.id ) == 'qemu';
 			}
 		}, {
			name: 'restart',
			label: this._( 'Restart' ),
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, '_changeState', 'RESTART'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, {
			name: 'clone',
			label: this._( 'Clone' ),
			isStandardAction: false,
			isMultiAction: false,
			callback: dojo.hitch(this, '_cloneDomain' ),
			canExecute: function(item) {
				return item.state == 'SHUTOFF';
			}
		}, {
			name: 'vnc',
			label: this._( 'View' ),
			isStandardAction: true,
			isMultiAction: false,
			iconClass: 'umcIconView',
			description: dojo.hitch( this, function( item ) {
				return dojo.replace( this._( 'Open a view to the virtual instance {label} on {nodeName}' ), item );
			} ),
			callback: dojo.hitch(this, 'vncLink' ),
			canExecute: function(item) {
				return ( item.state == 'RUNNING' || item.state == 'IDLE' ) && item.vnc;
			}
		}, {
			name: 'migrate',
			label: this._( 'Migrate' ),
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, '_migrateDomain' ),
			canExecute: function(item) {
				return item.state != 'PAUSE'; // FIXME need to find out if there are more than one node of this type
			}
		}, {
			name: 'add',
			label: this._( 'Create virtual instance' ),
			iconClass: 'umcIconAdd',
			isMultiAction: false,
			isContextAction: false,
			callback: dojo.hitch(this, '_addDomain' )
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
		this._finishedDeferred.then( dojo.hitch( this, function( ucr ) {
			this._grid = new umc.widgets.Grid({
				region: 'center',
				actions: actions,
				actionLabel: ucr[ 'uvmm/umc/action/label' ] != 'no', // hide labels of action columns
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
		} ) );
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
				this._finishedDeferred.then(dojo.hitch(this, function(ucr) {
					if (umc.tools.isTrue(ucr['uvmm/umc/autosearch'])) {
						this.filter();
					}
				}));
			}
		}));
	},

	vncLink: function( ids, items ) {
		umc.tools.umcpCommand( 'uvmm/domain/get', { domainURI : ids[ 0 ] } ).then( dojo.hitch( this, function( response ) {
			var w = window.open();
			var html = dojo.replace( "<html><head><title>{domainName} on {nodeName}</title></head><body><applet archive='/TightVncViewer.jar' code='com.tightvnc.vncviewer.VncViewer' height='100%%' width='100%%'><param name='host' value='{vncHost}' /><param name='port' value='{vncPort}' /><param name='offer relogin' value='no' /></applet></body></html>", {
				domainName: items[ 0 ].label,
				nodeName: items[ 0 ].nodeName,
				vncHost: response.result.data.vncHost,
				vncPort: response.result.data.vncPort
			} );
			w.document.write( html );
			w.document.close();
		} ) );
	},

	_migrateDomain: function( ids ) {
		var dialog = null, form = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var _migrate = dojo.hitch(this, function(name) {
			// send the UMCP command
			this.updateProgress(0, 1);
			umc.tools.umcpCommand('uvmm/domain/migrate', {
				domainURI: ids[ 0 ],
				targetNodeURI: name
			}).then(dojo.hitch(this, function() {
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}), dojo.hitch(this, function() {
				umc.dialog.alert(this._('An error ocurred during processing your request.'));
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}));
		});

		var sourceURI = ids[ 0 ].slice( 0, ids[ 0 ].indexOf( '#' ) );
		form = new umc.widgets.Form({
			widgets: [{
				name: 'name',
				type: 'ComboBox',
				label: this._('Please select the destination server:'),
				dynamicValues: function() {
					return umc.modules._uvmm.types.getNodes().then( function( items ) {
						return dojo.filter( items, function( item ) {
							return item.id != sourceURI;
						} );
					} );
				}
			}],
			buttons: [{
				name: 'submit',
				label: this._( 'Migrate' ),
				style: 'float: right;',
				callback: function() {
					var nameWidget = form.getWidget('name');
					if (nameWidget.isValid()) {
						var name = nameWidget.get('value');
						_cleanup();
						_migrate( name );
					}
				}
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ 'name' ]
		});

		dialog = new dijit.Dialog({
			title: this._('Migrate domain'),
			content: form
		});
		dialog.show();
	},

	_addDomain: function() {
		var wizard = null;

		var _cleanup = dojo.hitch(this, function() {
			this.selectChild(this._searchPage);
			this.removeChild(wizard);
			wizard.destroyRecursive();
		});

		var _finished = dojo.hitch(this, function(values) {
			this.standby(true);
			umc.tools.umcpCommand('uvmm/domain/add', {
				nodeURI: values.nodeURI,
				domain: values
			}).then(dojo.hitch(this, function() {
				_cleanup();
				this.standby(false);
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		});

		wizard = new umc.modules._uvmm.DomainWizard({
			onFinished: _finished,
			onCancel: _cleanup
		});
		this.addChild(wizard);
		this.selectChild(wizard);
	},

	_changeState: function(/*String*/ newState, ids) {
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

	_cloneDomain: function( ids ) {
		var dialog = null, form = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var _createClone = dojo.hitch(this, function(name) {
			// send the UMCP command
			this.updateProgress(0, 1);
			umc.tools.umcpCommand('uvmm/domain/clone', {
				domainURI: ids[ 0 ],
				cloneName: name
			}).then(dojo.hitch(this, function() {
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}), dojo.hitch(this, function() {
				umc.dialog.alert(this._('An error ocurred during processing your request.'));
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}));
		});

		form = new umc.widgets.Form({
			widgets: [{
				name: 'name',
				type: 'TextBox',
				label: this._('Please enter the name for the clone:'),
				regExp: '^[^./][^/]*$',
				invalidMessage: this._('A valid clone name cannot contain "/" and may not start with "." .')
			}],
			buttons: [{
				name: 'submit',
				label: this._('Create'),
				style: 'float: right;',
				callback: function() {
					var nameWidget = form.getWidget('name');
					if (nameWidget.isValid()) {
						var name = nameWidget.get('value');
						_cleanup();
						_createClone( name );
					}
				}
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ 'name' ]
		});

		dialog = new dijit.Dialog({
			title: this._('Create a clone'),
			content: form
		});
		dialog.show();
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
				width: 'adjust',
				formatter: dojo.hitch(this, 'cpuUsageFormatter')
			}, {
				name: 'memUsed',
				label: this._('Memory usage'),
				width: 'adjust',
				formatter: dojo.hitch(this, 'memoryUsageFormatter')
			}
];
		}

		// else type == 'domain'
		return [{
			name: 'label',
			label: this._('Name'),
			formatter: dojo.hitch(this, 'iconFormatter')
		}, {
			name: 'cpuUsage',
			label: this._('CPU usage'),
			style: 'min-width: 80px;',
			width: 'adjust',
			formatter: dojo.hitch(this, 'cpuUsageFormatter')
		}];
	},

	cpuUsageFormatter: function(id, rowIndex) {
		// summary:
		//		Formatter method for cpu usage.

		var item = this._grid._grid.getItem(rowIndex);
		var percentage = Math.round(item.cpuUsage);

		if (item.state == 'RUNNING' || item.state == 'IDLE') {
			// only show CPU info, if the machine is running
			return new dijit.ProgressBar({
				value: percentage + '%'
			});
		}

		return '';
	},

	memoryUsageFormatter: function(id, rowIndex) {
		// summary:
		//		Formatter method for memory usage.

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
			else if ( item.state == 'PAUSED' || ( item.state == 'SHUTOFF' && item.suspended ) ) {
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



