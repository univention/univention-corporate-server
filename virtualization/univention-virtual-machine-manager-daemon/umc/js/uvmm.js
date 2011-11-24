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
dojo.require("umc.render");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Tree");
dojo.require("umc.widgets.Tooltip");

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
			headerText: 'UCS Virtual Machine Manager'
			//helpText: this._('<p>This module provides a management interface for physical servers that are registered within the UCS domain.</p><p>The tree view on the left side shows an overview of all existing physical servers and the residing virtual instances. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual instance can be invoked on each of the instances.</p><p>Also possible is direct access to virtual instances. Therefor it must be activated in the configuration.</p><p>Each virtual instance entry in the tree view provides access to detailed information und gives the possibility to change the configuration or state and migrated it to another physical server.</p>')
		});
		this.addChild(this._searchPage);
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Search for virtual instances and physical servers'),
			design: 'sidebar'
		});
		this._searchPage.addChild(titlePane);

		//
		// add data grid
		//

		// search widgets
		var widgets = [{
			type: 'ComboBox',
			name: 'type',
			label: this._('Displayed type'),
			staticValues: [
				{ id: 'domain', label: this._('Virtual instance') },
				{ id: 'node', label: this._('Physical server') }
			],
			size: 'Half'
		}, {
			type: 'TextBox',
			name: 'pattern',
			label: this._('Query pattern'),
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
				actions: this._getGridActions('domain'),
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
		var menu = dijit.Menu({});
/*		menu.addChild(new dijit.MenuItem({
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
		}));*/
		menu.addChild(new dijit.MenuItem({
			label: this._( 'Reload' ),
			iconClass: 'umcIconRefresh',
			onClick: dojo.hitch(this, function() {
				this._tree.reload();
			})
		}));

		// when we right-click anywhere on the tree, make sure we open the menu
		menu.bindDomNode(this._tree.domNode);

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
				this.set( 'title', this.defaultTitle );
			}),
			moduleWidget: this
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
				vncHost: response.result.vncHost,
				vncPort: response.result.vncPort
			} );
			w.document.write( html );
			w.document.close();
		} ) );
	},

	_migrateDomain: function( ids ) {
		var dialog = null, form = null;
		var types = umc.modules._uvmm.types;

		if ( ids.length > 1 ) {
			var uniqueNodes = {}, count = 0;
			dojo.forEach( ids, function( id ) {
				var nodeURI = id.slice( 0, id.indexOf( '#' ) )
				if ( undefined === uniqueNodes[ nodeURI ] ) {
					++count;
				}
				uniqueNodes[ nodeURI ] = true;
			} );
			if ( count > 1 ) {
				umc.dialog.alert( this._( 'The selected virtual instances are not all located on the same physical server. The migration will not be performed.' ) );
				return;
			}
		}

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
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}));
		});

		var sourceURI = ids[ 0 ].slice( 0, ids[ 0 ].indexOf( '#' ) );
		var sourceScheme = types.getNodeType( sourceURI )
		form = new umc.widgets.Form({
			widgets: [{
				name: 'name',
				type: 'ComboBox',
				label: this._('Please select the destination server:'),
				dynamicValues: function() {
					return types.getNodes().then( function( items ) {
						return dojo.filter( items, function( item ) {
							return item.id != sourceURI && types.getNodeType( item.id ) == sourceScheme;
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
			content: form,
			'class': 'umcPopup'
		});
		dialog.show();
	},

	_removeDomain: function( ids, items ) {
		var dialog = null, form = null;
		var domain = items[ 0 ];
		var domain_details = null;
		var domainURI = ids[ 0 ];
		var widgets = [
			{
				type: 'Text',
				name: 'question',
				content: '<p>' + dojo.replace( this._( 'Should the selected virtual instance {label} be removed?' ), domain ) + '</p>',
				label: ''
			} ];
		var _widgets = null;
		var drive_list = [];

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var _remove = dojo.hitch( this, function() {
			this.updateProgress( 0, 1 );
			var volumes = [];
			umc.tools.forIn( form._widgets, dojo.hitch( this, function( iid, iwidget ) {
				if ( iwidget instanceof umc.widgets.CheckBox && iwidget.get( 'value' ) ) {
					volumes.push( iwidget.$id$ );
				}
			} ) );

			umc.tools.umcpCommand('uvmm/domain/remove', {
				domainURI: domainURI,
				volumes: volumes
			} ).then( dojo.hitch( this, function( response ) {
				this.updateProgress( 1, 1 );
				this.moduleStore.onChange();
			} ), dojo.hitch( this, function() {
				this.updateProgress( 1, 1 );
			} ) );
		} );

		// chain the UMCP commands for removing the domain
		var deferred = new dojo.Deferred();
		deferred.resolve();

		// get domain details
		deferred = deferred.then( dojo.hitch( this, function() {
			return umc.tools.umcpCommand('uvmm/domain/get', { domainURI : domainURI } );
		} ) );
		// find the default for the drive checkboxes;
		deferred = deferred.then( dojo.hitch( this, function( response ) {
			domain_details = response.result;
			var drive_list = dojo.map( response.result.disks, function( disk ) {
				return { domainURI : domainURI, pool : disk.pool, volumeFilename : disk.volumeFilename, source : disk.source };
			} );
			return umc.tools.umcpCommand('uvmm/storage/volume/deletable', drive_list );
		} ) );
		// got response for UMCP request
		deferred = deferred.then( dojo.hitch( this, function( response ) {
			var layout = [ 'question' ];
			var failed_disks = [];
			dojo.forEach( response.result, dojo.hitch( this, function( disk ) {

				if ( null !== disk.deletable ) {
					layout.push( disk.source );
					widgets.push( {
						type: 'CheckBox',
						name: disk.source,
						label: dojo.replace( this._( '{volumeFilename} (Pool: {pool})' ), disk ),
						value: disk.deletable,
						$id$: { pool : disk.pool, volumeFilename : disk.volumeFilename }
					} );
				} else {
					failed_disks.push( disk.source );
					disk.pool = null === disk.pool ? this._( 'Unknown' ) : disk.pool;
					widgets.push( {
						type: 'Text',
						name: disk.source,
						content: '<p>' + this._( 'Not removable' ) + ': ' + dojo.replace( this._( '{volumeFilename} (Pool: {pool})' ), disk ) + '</p>',
						label: '',
						$id$: { pool : disk.pool, volumeFilename : disk.volumeFilename }
					} );
				}
			} ) );
			if ( failed_disks.length ) {
				layout = layout.concat( failed_disks );
			}

			form = new umc.widgets.Form({
				widgets: widgets,
				buttons: [{
					name: 'submit',
					label: this._( 'delete' ),
					style: 'float: right;',
					callback: function() {
						_cleanup();
						_remove();
					}
				}, {
					name: 'cancel',
					label: this._('Cancel'),
					callback: _cleanup
				}],
				layout: layout
			});

			dialog = new dijit.Dialog({
				title: this._( 'Remove a virtual instance' ),
				content: form,
				'class' : 'umcPopup'
			});
			dialog.show();
		} ) );

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
				this.moduleStore.onChange();
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

	_maybeChangeState: function(/*String*/ question, /*String*/ buttonLabel, /*String*/ newState, ids) {
		var dialog = null, form = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var sourceURI = ids[ 0 ].slice( 0, ids[ 0 ].indexOf( '#' ) );
		form = new umc.widgets.Form({
			widgets: [{
				name: 'question',
				type: 'Text',
				content: '<p>' + question + '</p>'
			}],
			buttons: [{
				name: 'submit',
				label: buttonLabel,
				style: 'float: right;',
				callback: dojo.hitch( this, function() {
					_cleanup();
					this._changeState( newState, ids );
				} )
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ 'question' ]
		});

		dialog = new dijit.Dialog({
			title: this._('Migrate domain'),
			content: form,
			'class': 'umcPopup',
			style: 'max-width: 400px;'
		});
		dialog.show();
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
		}), dojo.hitch(this, function(error) {
			this.modulestore.onChange();
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

		var _createClone = dojo.hitch(this, function( name, mac_address ) {
			// send the UMCP command
			this.updateProgress(0, 1);
			umc.tools.umcpCommand('uvmm/domain/clone', {
				domainURI: ids[ 0 ],
				cloneName: name,
				macAddress: mac_address
			}).then(dojo.hitch(this, function() {
				this.moduleStore.onChange();
				this.updateProgress(1, 1);
			}), dojo.hitch(this, function(error) {
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
			}, {
				name: 'mac_address',
				type: 'ComboBox',
				label: this._( 'MAC addresses' ),
				staticValues: [
					{ id : 'clone', label : this._( 'Inherit MAC addresses' ) },
					{ id : 'auto', label : this._( 'Generate new MAC addresses' ) }
				]
			} ],
			buttons: [{
				name: 'submit',
				label: this._('Create'),
				style: 'float: right;',
				callback: function() {
					var nameWidget = form.getWidget('name');
					var macWidget = form.getWidget('mac_address');
					if (nameWidget.isValid()) {
						var name = nameWidget.get('value');
						_cleanup();
						_createClone( name, macWidget.get( 'value' ) );
					}
				}
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ 'name', 'mac_address' ]
		});

		dialog = new dijit.Dialog({
			title: this._('Create a clone'),
			content: form,
			'class': 'umcPopup'
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

	_getGridActions: function(type) {
		var types = umc.modules._uvmm.types;

		if (type == 'node') {
			// we do not have any actions for nodes
			return [];
		}

		// else type == 'domain'
		// STATES = ( 'NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED' )
		return [{
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
			callback: dojo.hitch(this, '_maybeChangeState', this._( 'Stopping virtual instances will turn them off without shutting down the operating system. Should the operation be continued?' ), this._( 'Stop' ), 'SHUTDOWN'),
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
 			label: this._( 'Suspend' ),
 			// iconClass: 'umcIconPause',
 			isStandardAction: false,
 			isMultiAction: true,
 			callback: dojo.hitch(this, '_changeState', 'SUSPEND'),
 			canExecute: function(item) {
 				return ( item.state == 'RUNNING' || item.state == 'IDLE' ) && types.getNodeType( item.id ) == 'qemu';
 			}
 		}, /* { FIXME: not yet fully supported
			name: 'restart',
			label: this._( 'Restart' ),
			isStandardAction: false,
			isMultiAction: true,
			callback: dojo.hitch(this, '_changeState', 'RESTART'),
			canExecute: function(item) {
				return item.state == 'RUNNING' || item.state == 'IDLE';
			}
		}, */ {
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
			name: 'remove',
			label: this._( 'Remove' ),
			isStandardAction: false,
			isMultiAction: false,
			callback: dojo.hitch(this, '_removeDomain' ),
			canExecute: function(item) {
				return item.state == 'SHUTOFF';
			}
		}, {
			name: 'add',
			label: this._( 'Create virtual instance' ),
			iconClass: 'umcIconAdd',
			isMultiAction: false,
			isContextAction: false,
			callback: dojo.hitch(this, '_addDomain' )
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
		var html = dojo.string.substitute('<img src="images/icons/16x16/${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${label}', {
			icon: this._iconClass(item),
			height: '16px',
			width: '16px',
			label: label
		});
		var widget = new umc.widgets.Text( {
			content: html
		} );
		if ( undefined !== item.state ) {
			var tooltip = new umc.widgets.Tooltip( {
				label: dojo.replace( this._( 'State: {state}<br>Server: {node}' ), {
					state: umc.modules._uvmm.types.getDomainStateDescription( item ),
					node: item.nodeName
				} ),
				connectId: [ widget.domNode ],
				position: 'below'
			});

			// destroy the tooltip when the widget is destroyed
			tooltip.connect( widget, 'destroy', 'destroy' );
		}

		return widget;
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

		// update tree
		if ( treeType == 'node' && treeID ) {
			umc.tools.umcpCommand( 'uvmm/node/query', { nodePattern: treeID } ).then( dojo.hitch( this, function( response ) {
				this._tree.model.changes( response.result );
			} ) );
		} else if ( treeType == 'group' ) {
			umc.tools.umcpCommand( 'uvmm/node/query', { nodePattern: "*" } ).then( dojo.hitch( this, function( response ) {
				this._tree.model.changes( response.result );
			} ) );
		}
		// update the grid columns
		this._grid.setColumnsAndActions(this._getGridColumns(vals.type), this._getGridActions(vals.type));
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



