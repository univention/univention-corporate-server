/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define, window, require, console, document*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/_base/window",
	"dojo/dom-class",
	"dojo/window",
	"dojo/string",
	"dojo/query",
	"dojo/Deferred",
	"dojo/topic",
	"dojo/on",
	"dojo/aspect",
	"dojo/promise/all",
	"dojo/sniff",
	"dojox/html/entities",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/ProgressBar",
	"dijit/Dialog",
	"dijit/form/_TextBoxMixin",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/Tree",
	"umc/widgets/Tooltip",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/Button",
	"umc/modules/uvmm/GridUpdater",
	"umc/modules/uvmm/TreeModel",
	"umc/modules/uvmm/DomainPage",
	"umc/modules/uvmm/DomainWizard",
	"umc/modules/uvmm/InstancePage",
	"umc/modules/uvmm/InstanceWizard",
	"umc/modules/uvmm/CreatePage",
	"umc/modules/uvmm/types",
	"umc/modules/uvmm/snapshot",
	"umc/i18n!umc/modules/uvmm",
	"xstyle/css!./uvmm.css"
], function(
	declare, lang, array, kernel, win, domClass, dojoWindow, string, query, Deferred, topic, on, aspect,
	all, has, entities, Menu, MenuItem, ProgressBar, Dialog, _TextBoxMixin,
	tools, dialog, Module, Page, Form, Grid, SearchForm, Tree, Tooltip, Text, ContainerWidget,
	CheckBox, ComboBox, TextBox, Button, GridUpdater, TreeModel, DomainPage, DomainWizard,
	InstancePage, InstanceWizard, CreatePage, types, snapshot, _
) {

	var isRunning = function(item) {
		// isRunning contains state==PAUSED to enable VNC Connections to pause instances
		return (item.state === 'RUNNING' || item.state === 'IDLE' || item.state === 'PAUSED') && item.node_available && !isPausedForMigration(item);
	};

	var isPaused = function(item) {
		return (item.state === 'PAUSED') && item.node_available;
	};

	var isPausedForMigration = function(item) {
		//  2 Normal migration (Paused on target)
		// 12 Postcopy migration (Paused on source)
		return isPaused(item) && [2, 12].indexOf(item.reason) !== -1;
	};

	var isPausedForSnapshot = function(item) {
		return isPaused(item) && item.reason === 3;
	};

	var canStart = function(item) {
		return item.node_available && (item.state !== 'RUNNING' && item.state !== 'IDLE' && !isTerminated(item) && item.state !== 'PENDING') && !isPausedForMigration(item) && !isPausedForSnapshot(item);
	};

	var canVNC = function(item) {
		return isRunning(item) && item.vnc;
	};

	var isTerminated = function(item) {
		return item.state === 'TERMINATED';
	};

	var isEC2 = function(item) {
		return item.u_connection_type === 'EC2';
	};

	var isOpenStack = function(item) {
		return item.u_connection_type === 'OpenStack';
	};

	return declare("umc.modules.uvmm", [ Module ], {

		// the property field that acts as unique identifier
		idProperty: 'id',

		// internal reference to the search page
		_searchPage: null,

		// internal reference to the detail page for editing an UDM object
		_domainPage: null,

		selectablePagesToLayoutMapping: {
			'_searchPage': 'searchpage-grid-and-tree',
			'_domainPage': 'uvmm-detailpage'
		},

		// reference to a `umc.widgets.Tree` instance which is used to display the container
		// hierarchy for the UDM navigation module
		_tree: null,

		// reference to the last item in the navigation on which a context menu has been opened
		_navContextItem: null,

		_finishedDeferred: null,
		_ucr: null,

		_progressBar: null,
		_progressContainer: null,

		// open this domain by default
		openDomain: null,

		// internal flag to indicate that GridUpdater should show a notification
		_itemCountChangedNoteShowed: false,

		// internal field to store the current width of the viewport
		_currentWidth: null,

		// internal constant to decide which GridColumns should be displayed for domain vms
		_GRID_COLUMNS_WIDTH_LIMIT: 550,

		// internal Deferred to control the rate of updating _currentWidth
		_resizeDeferred: null,

		// used to catch context events on the tooltip
		_contextCatcher: null,

		uninitialize: function() {
			this.inherited(arguments);

			if (this._progressContainer) {
				this._progressContainer.destroyRecursive();
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			// call superclass method
			this.inherited(arguments);

			// load asynchronously some UCR variables
			this._finishedDeferred = new Deferred();
			tools.ucr('uvmm/umc/*').then(lang.hitch(this, function(ucr) {
				this._ucr = ucr;
				this._finishedDeferred.resolve(this._ucr);
			}));

			// directly open domain
			if (this.openDomain) {
				this._domainPage = new DomainPage({
					isClosable: true,
					moduleWidget: this,
					addNotification: lang.hitch(this, 'addNotification'),
					addWarning: lang.hitch(this, 'addWarning')
				});
				this._domainPage.on('closeTab', lang.hitch(this, 'closeDomainPage'));
				this.addChild(this._domainPage);
				this.selectChild(this._domainPage);
				this.openDomainPage(this.openDomain);
				return; // do not render the overview page
			}

			// setup search page
			this._searchPage = new Page({
				headerText: 'UCS Virtual Machine Manager'
				//helpText: _('<p>This module provides a management interface for physical servers that are registered within the UCS domain.</p><p>The tree view on the left side shows an overview of all existing physical servers and the residing virtual machines. By selecting one of the physical servers statistics of the current state are displayed to get an impression of the health of the hardware system. Additionally actions like start, stop, suspend and resume for each virtual machine can be invoked on each of the instances.</p><p>Also possible is direct access to virtual machines. Therefore it must be activated in the configuration.</p><p>Each virtual machine entry in the tree view provides access to detailed information and gives the possibility to change the configuration or state and migrated it to another physical server.</p>')
			});
			this.addChild(this._searchPage);

			//
			// add data grid
			//

			// search widgets
			var widgets = [{
				type: ComboBox,
				name: 'type',
				label: _('Displayed type'),
				staticValues: [
					{ id: 'domain', label: _('Virtual machine') },
					{ id: 'node', label: _('Physical server') },
					{ id: 'instance', label: _('Cloud instance') }
					//{ id: 'cloud', label: _('Cloud connection') }
				],
				size: 'One'
			}, {
				type: TextBox,
				name: 'pattern',
				label: _('Query pattern'),
				size: 'One',
				value: ''
			}];
			var layout = [[ 'type', 'pattern', 'submit' ]];

			// generate the search widget
			this._searchForm = new SearchForm({
				region: 'main',
				widgets: widgets,
				layout: layout,
				onSearch: lang.hitch(this, 'filter')
			});
			this._searchPage.addChild(this._searchForm);

			// generate the data grid
			this._finishedDeferred.then( lang.hitch( this, function( ucr ) {
				this._grid = new Grid({
					region: 'main',
					actions: this._getGridActions('domain'),
					columns: this._getGridColumns('domain'),
					moduleStore: this.moduleStore
				});

				this._searchPage.addChild(this._grid);

				this._grid._grid.on('StyleRow', lang.hitch(this, '_adjustIconColumns'));
				this._grid.on('FilterDone', lang.hitch(this, function() {
					if (!this._tree._getFirst()) {
						this._tree.reload();
					}
				}));

				// setup autoUpdater
				this._gridUpdater = new GridUpdater({
					grid: this._grid,
					tree: this._tree,
					interval: parseInt(ucr['uvmm/umc/autoupdate/interval'], 10),
				});
				this.own(this._gridUpdater);

			} ) );
			// generate the navigation tree
			var model = new TreeModel({
				umcpCommand: lang.hitch(this, 'umcpCommand')
			});
			this._tree = new Tree({
				region: 'nav',
				model: model,
				persist: false,
				showRoot: false,
				autoExpand: true,
				path: [ model.root.id ],
				// customize the method getIconClass()
				//onClick: lang.hitch(this, 'filter'),
				getIconClass: lang.hitch(this, function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return tools.getIconClass(this._iconClass(item)) + ' uvmm-tree-icon';
				}),
				getTooltip: lang.hitch(this, function(item) {
					return this._getTreeTooltip(item);
				})
			});
			this._tree.dndController.singular = true;
			this._searchPage.addChild(this._tree);

			// add a context menu to edit/delete items
			var menu = new Menu({});
			// TODO: Bug #36272
			/*menu.addChild(new MenuItem({
				label: _( 'Edit' ),
				iconClass: 'umcIconEdit',
				onClick: lang.hitch(this, function(e) {
					if(this._navContextItem) {
						if(this._navContextItem.type == 'cloud' && this._navContextItem.dn) {
							require('umc/app').openModule('udm', 'uvmm/cloudconnection',{'openObject': {'objectDN': this._navContextItem.dn, 'objectType': 'uvmm/cloudconnection'}});
						} else if(this._navContextItem.type == 'cloud' || (this._navContextItem.type == 'group' && this._navContextItem.id == 'cloudconnections')) {
							require('umc/app').openModule('udm', 'uvmm/cloudconnection');
						}
					}
				})}));
			menu.addChild(new MenuItem({
				label: _( 'Delete' ),
				iconClass: 'umcIconDelete',
				onClick: lang.hitch(this, function() {
					this.removeObjects(this._navContextItem.id);
				})
			}));*/
			menu.addChild(new MenuItem({
				label: _( 'Reload' ),
				iconClass: 'umcIconRefresh',
				onClick: lang.hitch(this, function() {
					this._tree.reload();
				})
			}));
			this._tree.own(menu);

			// tree left-click
			this.own(aspect.after(this._tree, '_onClick', lang.hitch(this, function(node) {
				this._navContextItem = node.item;
			}), true));
			// tree right-click for edit menu
			this.own(aspect.after(this._tree, '_onNodeMouseEnter', lang.hitch(this, function(node) {
				this._navContextItemFocused = node.item;
			}), true));
			this.own(aspect.before(menu, '_openMyself', lang.hitch(this, function() {
				this._navContextItem = this._navContextItemFocused;
			})));

			// when we right-click anywhere on the tree, make sure we open the menu
			menu.bindDomNode(this._tree.domNode);

			// remember on which item the context menu has been opened
			/*aspect.after(menu, '_openMyself', lang.hitch(this, function(e) { // TODO: require dojo/aspect if uncomment
				var el = registry.getEnclosingWidget(e.target); // TODO: require dijit/registry if uncomment
				if (el) {
					this._navContextItem = el.item;
				}
			}));*/

			this._searchPage.startup();

			// setup a progress bar with some info text
			this._progressContainer = new ContainerWidget({});
			this._progressBar = new ProgressBar({
				style: 'background-color: #fff;'
			});
			this._progressContainer.addChild(this._progressBar);
			this._progressContainer.addChild(new Text({
				content: _('Please wait, your requests are being processed...')
			}));

			// setup the detail page
			this._domainPage = new DomainPage({
				onCloseTab: lang.hitch(this, function() {
					this.selectChild(this._searchPage);
					this.set( 'title', this.defaultTitle );
				}),
				moduleWidget: this,
				addNotification: lang.hitch(this, 'addNotification'),
				addWarning: lang.hitch(this, 'addWarning')
			});
			this.addChild(this._domainPage);

			// register events
			this._domainPage.on('UpdateProgress', lang.hitch(this, 'updateProgress'));
		},

		postCreate: function() {
			this.inherited(arguments);

			this.own(on(win.doc, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
			this._currentWidth = dojoWindow.getBox().w;

			if (this._tree) {
				on.once(this._tree, 'load', lang.hitch(this, function() {
					if (this._tree._getFirst() && this._tree._getFirst().item.id === 'cloudconnections') {
						this._searchForm.getWidget('type').set('value', 'instance');
					}
					this.own(this._tree.watch('path', lang.hitch(this, function(attr, oldVal, newVal) {
						if (tools.isEqual(oldVal, newVal)) {
							return;
						}
						var searchType = this._searchForm.getWidget('type').get('value');
						if (searchType === 'domain' || searchType === 'instance') {
							this.filter();
						}
					})));
					this.own(aspect.after(this._searchPage, '_onShow', lang.hitch(this, function() {
						this._selectInputText();
						this.filter();
					})));
					this._selectInputText();
					this._finishedDeferred.then(lang.hitch(this, function(ucr) {
						if (tools.isTrue(ucr['uvmm/umc/autosearch'])) {
							this.filter();
						}
					}));
					if (this._tree._getLast().item.type === 'root') {
						var version = tools.status('ucsVersion').split('-')[0];
						dialog.alert(_('A connection to a virtualization infrastructure could not be established. You can either connect to a public or private cloud. Alternatively you can install a hypervisor on this or on any other UCS server in this domain. Further details about the virtualization can be found in <a target="_blank" href="https://docs.software-univention.de/manual-%s.html#uvmm:chapter">the manual</a>.', version));
					}
				}));
			}

			this.on('close', lang.hitch(this, 'onCloseTab'));
		},

		_handleResize: function(evt) {
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}
			this._resizeDeferred = tools.defer(lang.hitch(this, function() {
				var type = this._searchForm.get('value').type;
				if (type === 'domain') {
					this._currentWidth = dojoWindow.getBox().w;
					this.updateGrid(type);
				}
			}), 200);
			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */});
		},

		_selectInputText: function() {
			// focus on input widget
			var widget = this._searchForm.getWidget('pattern');
			widget.focus();

			// select the text
			if (widget.textbox) {
				try {
					_TextBoxMixin.selectInputText(widget.textbox);
				}
				catch (err) { }
			}
		},

		vncLink: function( ids, items ) {
			array.forEach(items, function(item) {
				var id = item.id;
				var uuid = encodeURIComponent(id.slice(id.indexOf('#') + 1));
				var port = window.location.port ? ':' + window.location.port : '';
				var title = encodeURIComponent(item.label + '@' + item.nodeName);
				var url = window.location.protocol + '//' + window.location.host + port + '/univention-novnc/vnc_auto.html?port=6080&path=?token=' + uuid + '&title=' + title;
				window.open(url, '_blank');
			});
		},

		_hasErrorMsg: function(item) {
			if (item.hasOwnProperty('error') && item.error.hasOwnProperty('msg')) {
				return !!item.error.msg;
			}
			return false;
		},

		_hasMigrationMsg: function(item) {
			if (item.hasOwnProperty('migration') && item.migration.hasOwnProperty('msg')) {
				return !!item.migration.msg;
			}
			return false;
		},

		_isMigrating: function(item) {
			// 1: VIR_DOMAIN_JOB_BOUNDED
			// 2: VIR_DOMAIN_JOB_UNBOUNDED
			var runningMigrationTypes = [1, 2];
			return this._hasMigrationMsg(item) &&
				item.migration.hasOwnProperty('type') &&
				runningMigrationTypes.indexOf(item.migration.type) !== -1;
		},

		_migrate: function(ids, items) {
			if (items.length > 1) {
				console.error("Migrating multiple machines is not supported at the moment");
				return;
			}
			if (this._isMigrating(items[0])) {
				this._migrateStatus(ids, items);
			} else {
				this._migrateDomain(ids, items);
			}
		},

		_getLocalizedMigrationMsg: function(migration) {
			return lang.replace(
				_('Migration in progress since {time_elapsed} sec, iteration {memory_iteration}'),
				function(_, key) {
					if (key === 'time_elapsed') {
						return migration[key] / 1000;
					}
					return migration[key];
				}
			);
		},

		_migrateStatus: function(ids, items) {
			var _dialog = null;
			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
			};
			var localizedMigrationMsg = this._getLocalizedMigrationMsg(items[0].migration);

			var form = new Form({
				style: 'max-width: 500px;',
				widgets: [ {
					type: Text,
					name: 'status',
					content: _('<p>This machine is currently being migrated.</p><p>%s</p>', localizedMigrationMsg),
				}],
				buttons: [{
					name: 'abort',
					label: _( 'Abort migration' ),
					focused: false,
					tabindex: 2,
					callback: lang.hitch(this, function() {
						tools.umcpCommand('uvmm/domain/migrate', {
						domainURI: ids[ 0 ],
						mode: -1
						});
						this._grid._grid.deselect(ids[0]);
						_cleanup();
					})
				}, {
					name: 'postcopy',
					label: _( 'Switch to postcopy' ),
					focused: false,
					tabindex: 3,
					callback: lang.hitch(this, function() {
						tools.umcpCommand('uvmm/domain/migrate', {
						domainURI: ids[ 0 ],
						mode: 101
						});
						this._grid._grid.deselect(ids[0]);
						_cleanup();
					})
				}, {
					name: 'cancel',
					label: _('Close'),
					callback: _cleanup,
					tabindex: 1,
					defaultButton: true
				}],
				layout: [ 'status', ['postcopy', 'abort'] ]
			});

			_dialog = new Dialog({
				title: _('Migrate domain'),
				content: form,
				'class': 'umcPopup'
			});

			_dialog.show();
		},

		_migrateDomain: function(ids, domains) {
			var _dialog = null, form = null;
			var unavailable = array.some(domains, function( domain ) {
				return domain.node_available === false;
			} );

			all({
				targethosts: tools.umcpCommand('uvmm/targethost/query', { domainURI: ids[0] }),
				nodes: types.getNodes()
			}).then(lang.hitch(this, function(results) {
				var items = results.nodes;
				var targethosts = array.map(results.targethosts.result, function(targethost) {
					return targethost.id;
				});
				var _cleanup = function() {
					_dialog.hide();
					_dialog.destroyRecursive();
				};

				var _migrate = lang.hitch(this, function(name) {
					// send the UMCP command
					tools.umcpCommand('uvmm/domain/migrate', {
						domainURI: ids[ 0 ],
						targetNodeURI: name
					}).then(lang.hitch(this, function() {
						this._grid.update();
					}), lang.hitch(this, function() {
						this._grid.update();
					}));
				});

				var sourceURI = ids[ 0 ].slice( 0, ids[ 0 ].indexOf( '#' ) );
				var sourceScheme = types.getNodeType( sourceURI );

				var validHosts = array.filter( items, function( item ) {
					if (targethosts.length > 0) {
						// if targethosts are defined, offline targethosts have to be filtered, too
						return targethosts.indexOf(item.label) != -1 && item.available && item.id != sourceURI && types.getNodeType( item.id ) == sourceScheme;
					} else {
						return item.id != sourceURI && types.getNodeType( item.id ) == sourceScheme;
					}
				} );
				var numberOfValidHosts = validHosts.length;

				form = new Form({
					style: 'max-width: 500px;',
					widgets: [ {
						type: Text,
						name: 'warning',
						visible: unavailable,
						content: _( '<p>For fail over the virtual machine can be migrated to another physical server re-using the last known configuration and all disk images. This can result in <strong>data corruption</strong> if the images are <strong>concurrently used</strong> by multiple running machines! Therefore the failed server <strong>must be blocked from accessing the image files</strong>, for example by blocking access to the shared storage or by disconnecting the network.</p><p>When the server is restored, all its previous virtual machines will be shown again. Any duplicates have to be cleaned up manually by migrating the machines back to the server or by deleting them. Make sure that shared images are not delete.</p>' )
					}, {
						type: Text,
						name: 'warning_ram',
						visible: false,
						depends: ['name'],
						content: '<p>' + _('<b>Warning:</b> Memory size exceeds currently available RAM on node. Migrating the VM may degrade the performance of the host and all other VMs.') + '</p>'
					}, {
						name: 'name',
						type: ComboBox,
						label: _('Please select the destination server:'),
						staticValues: validHosts,
						sortStaticValues: true,
						onChange: function(value, widgets) {
							array.forEach(widgets.name.staticValues, function(host) {
								if (host.id === value) {
									widgets.warning_ram.set('visible', (host.memPhysical - host.memUsed <= domains[0].mem) || true);
									return false;
								}
							});
						}
					}],
					buttons: [{
						name: 'cancel',
						label: _('Cancel'),
						callback: _cleanup
					}, {
						name: 'submit',
						label: _( 'Migrate' ),
						callback: lang.hitch(this, function() {
							var nameWidget = form.getWidget('name');
							if (nameWidget.isValid()) {
								var name = nameWidget.get('value');
								_cleanup();
								this._grid._grid.deselect(ids[0]);
								_migrate( name );
							}
						})
					}],
					layout: [ 'warning', 'warning_ram', 'name' ]
				});

				_dialog = new Dialog({
					title: _('Migrate domain'),
					content: form,
					'class': 'umcPopup'
				});

				if (numberOfValidHosts === 0) {
					form._buttons.submit.set('disabled', true);
				}

				_dialog.show();
			}));
		},

		_removeDomain: function( ids, items ) {
			var _dialog = null, form = null;
			var domain = items[ 0 ];
			var domainURI = ids[ 0 ];
			var widgets = [
				{
					type: Text,
					name: 'question',
					content: '<p>' + lang.replace( _( 'Should the selected virtual machine {label} be removed?' ), {
						label: entities.encode(domain.label)
					} ) + '</p>',
					label: ''
				} ];

			var _cleanup = function() {
				_dialog.hide();
				form.destroyRecursive();
			};

			var _remove = lang.hitch( this, function() {
				this.showProgress();
				var volumes = [];
				tools.forIn( form._widgets, lang.hitch( this, function( iid, iwidget ) {
					if ( iwidget instanceof CheckBox && iwidget.get( 'value' ) ) {
						volumes.push(iwidget.name);
					}
				} ) );

				tools.umcpCommand('uvmm/domain/remove', {
					domainURI: domainURI,
					volumes: volumes
				} ).then( lang.hitch( this, function( response ) {
					this.hideProgress();
					this.moduleStore.onChange();
				} ), lang.hitch( this, function() {
					this.hideProgress();
				} ) );
			} );

			// chain the UMCP commands for removing the domain
			var deferred = new Deferred();
			deferred.resolve();

			// get domain details
			deferred = deferred.then( lang.hitch( this, function() {
				return tools.umcpCommand('uvmm/domain/get', { domainURI : domainURI } );
			} ) );
			// find the default for the drive checkboxes;
			deferred = deferred.then( lang.hitch( this, function( response ) {
				var drive_list = array.map( response.result.disks, function( disk ) {
					return {
						domainURI: domainURI,
						pool: disk.pool,
						source: disk.source,
						volumeFilename: disk.volumeFilename
						};
				} );
				return tools.umcpCommand('uvmm/storage/volume/deletable', drive_list );
			} ) );
			// got response for UMCP request
			deferred = deferred.then( lang.hitch( this, function( response ) {
				var layout = [ 'question' ];
				var failed_disks = [];
				array.forEach( response.result, lang.hitch( this, function( disk ) {
					if (null === disk.pool) {
						return;
					} else if (null !== disk.deletable) {
						layout.push( disk.source );
						widgets.push( {
							type: CheckBox,
							name: disk.source,
							label: lang.replace( _( '{volumeFilename} (Pool: {pool})' ), disk ),
							value: disk.deletable
						} );
					} else {
						failed_disks.push( disk.source );
						disk.pool = null === disk.pool ? _( 'Unknown' ) : disk.pool;
						widgets.push( {
							type: Text,
							name: disk.source,
							content: '<p>' + _( 'Not removable' ) + ': ' + lang.replace( _( '{volumeFilename} (Pool: {pool})' ), {
								volumeFilename: entities.encode(disk.volumeFilename),
								pool: entities.encode(disk.pool)
							} ) + '</p>',
							label: ''
						} );
					}
				} ) );
				if ( failed_disks.length ) {
					layout = layout.concat( failed_disks );
				}

				form = new Form({
					widgets: widgets,
					buttons: [{
						name: 'cancel',
						label: _('Cancel'),
						callback: _cleanup
					}, {
						name: 'submit',
						label: _( 'Delete' ),
						callback: function() {
							_cleanup();
							_remove();
						}
					}],
					layout: layout
				});

				_dialog = new Dialog({
					title: _( 'Delete a virtual machine' ),
					content: form,
					'class' : 'umcPopup'
				});
				_dialog.show();
			} ) );

		},

		_removeInstance: function( ids, items ) {
			var _dialog = null, form = null;
			var domain = items[ 0 ];
			var domainURI = ids[ 0 ];
			var widgets = [
				{
					type: Text,
					name: 'question',
					content: '<p>' + lang.replace( _( 'Should the selected instance {label} be deleted?' ), {
						label: entities.encode(domain.label)
					} ) + '</p>',
					label: ''
				} ];
			var layout = [ 'question' ];

			var _cleanup = function() {
				_dialog.hide();
				form.destroyRecursive();
			};

			var _remove = lang.hitch( this, function() {
				this.showProgress();

				tools.umcpCommand('uvmm/instance/remove', {
					domainURI: domainURI
				} ).then( lang.hitch( this, function( response ) {
					this.hideProgress();
					this.moduleStore.onChange();
				} ), lang.hitch( this, function() {
					this.hideProgress();
				} ) );
			} );

			form = new Form({
				widgets: widgets,
				buttons: [{
					name: 'cancel',
					label: _('Cancel'),
					callback: _cleanup
				}, {
					name: 'submit',
					label: _( 'Delete' ),
					callback: function() {
						_cleanup();
						_remove();
					}
				}],
				layout: layout
			});

			_dialog = new Dialog({
				title: _( 'Delete an instance' ),
				content: form,
				'class' : 'umcPopup'
			});
			_dialog.show();

		},

		openCreatePage: function() {
			var page = null;

			var _cleanup = lang.hitch(this, function() {
				this.selectChild(this._searchPage);
				this.removeChild(page);
				page.destroyRecursive();
			});

			var _finished = lang.hitch(this, function(values) {
				_cleanup();
				var func = {
					'domain': lang.hitch(this, '_addDomain'),
					'cloud': lang.hitch(this, '_addCloudConnection'),
					'instance': lang.hitch(this, '_addInstance')
				}[values.type];
				if (func) {
					func(values);
				}
			});

			page = new CreatePage({
				item: this._navContextItem,
				onCancel: _cleanup,
				onFinished: _finished,
				umcpCommand: lang.hitch(this, 'umcpCommand')
			});
			this.addChild(page);
			this.selectChild(page);
		},

		_addDomain: function(values) {
			var wizard = null;

			var _cleanup = lang.hitch(this, function() {
				this.selectChild(this._searchPage);
				this.removeChild(wizard);
				wizard.destroyRecursive();
			});

			var _finished = lang.hitch(this, function(values) {
				this.standbyDuring(tools.umcpCommand('uvmm/domain/add', {
					nodeURI: values.nodeURI,
					domain: values
				}).then(lang.hitch(this, function() {
					_cleanup();
					this.moduleStore.onChange();
				})));
			});

			wizard = new DomainWizard({
				onFinished: _finished,
				onCancel: _cleanup,
				nodeURI: values.nodeURI
			});
			this.addChild(wizard);
			this.selectChild(wizard);
		},

		_addCloudConnection: function(values) {
			var wizard = null;

			var _cleanup = lang.hitch(this, function() {
				this.selectChild(this._searchPage);
				this.removeChild(wizard);
				wizard.destroyRecursive();
			});

			var _finished = lang.hitch(this, function(response, values) {
				// add cloud connection
				var max = 60;
				this.showProgress();
				// wait for available connection
				var counter = 1;
				var deferred = new Deferred();
				var wait = lang.hitch(this, function() {
					tools.umcpCommand('uvmm/cloud/query', {"nodePattern": values.name}, false).then(lang.hitch(this, function(result) {
						var connection = array.filter(result.result, function(item) {
							return item.label == values.name;
						});
						counter += 1;
						if (connection[0].available) {
							this.hideProgress();
							deferred.resolve();
							_cleanup();
							this._tree.reload();
						}
						if (counter >= max) {
							this.hideProgress();
							deferred.resolve();
							_cleanup();
							this._tree.reload();
						}
						if (!deferred.isResolved()) {
							tools.defer(wait, 1000);
						}
					}));
				});
				tools.defer(wait, 1000);
			});

			this.loadWizardPages(values.cloudtype).then(lang.hitch(this, function(Wizard) {
				wizard = new Wizard({
					autoValidate: true,
					onFinished: _finished,
					onCancel: _cleanup,
					moduleStore: this.moduleStore,
					cloudtype: values.cloudtype,
					standby: this.standby
				});
				this.addChild(wizard);
				this.selectChild(wizard);
			}));
		},

		loadWizardPages: function(cloud) {
			var deferred = new Deferred();
			require(['umc/modules/uvmm/' + cloud], function(wizard) {
				deferred.resolve(wizard);
			});
			return deferred;
		},

		_addInstance: function(values) {
			var wizard = null;
			var _cleanup = lang.hitch(this, function() {
				this.selectChild(this._searchPage);
				this.removeChild(wizard);
				wizard.destroyRecursive();
				this.filter();
			});

			var _finished = lang.hitch(this, function(values) {
				// add cloud instance
				var addFailed = false;
				var max = 60;
				this.showProgress();
				tools.umcpCommand('uvmm/instance/add', {
					conn_name: values.cloud,
					name: values.name,
					parameter: values
				}).then( lang.hitch( this, function( response ) {
					this.moduleStore.onChange();
				}), lang.hitch( this, function() {
					this.hideProgress();
					addFailed = true; // failed umcp will display an error message, but the wizard should still be open.
				}));
				// wait for running instance
				var counter = 1;
				var deferred = new Deferred();
				var wait = lang.hitch(this, function() {
					tools.umcpCommand('uvmm/instance/query', {"nodePattern": values.cloud, "domainPattern": values.name}, false).then(lang.hitch(this, function(result) {
						var connection = array.filter(result.result, function(item) {
							return item.label == values.name;
						});
						counter += 1;
						if (connection[0] && connection[0].state == "RUNNING") {
							this.hideProgress();
							deferred.resolve();
							_cleanup();
						}
						if (addFailed) {
							this.hideProgress();
							deferred.resolve();
						}
						if (counter >= max) {
							this.hideProgress();
							deferred.resolve();
							_cleanup();
							this.addNotification(lang.replace( _( 'The instance {label} is still not running. Please wait and to update the view, click on "Search".' ), {label: entities.encode(values.name)} ));
						}
						if (!deferred.isResolved()) {
							tools.defer(wait, 1000);
						}
						this.filter();
					}));
				});
				tools.defer(wait, 1000);
			});

			var cloud = {
				name: values.cloud,
				type: values.cloudtype
			};
			wizard = new InstanceWizard({
				onFinished: _finished,
				onCancel: _cleanup,
				cloud: cloud
			});
			this.addChild(wizard);
			this.selectChild(wizard);
		},

		_shutdown: function(ids, items) {
			tools.getUserPreferences().then(lang.hitch(this, function(prefs) {
				if (tools.isTrue(prefs.uvmmShutdownSeen)) {
					this._changeState('SHUTDOWN', 'shutdown', ids, items);
				} else {
					dialog.confirmForm({
						title: _('Virtual machine shutdown'),
						widgets: [
							{
								type: Text,
								name: 'info_text',
								content: _('<p>Shutting down virtual machines cleanly required the cooperation of their guest operating system.</p><p>For KVM ACPI must be enabled.</p><p>If the operating system does not cooperate, "Stop" can be used to forcefully turn off the virtual machine.</p>')
							}, {
								type: CheckBox,
								value: true,
								name: 'show_again',
								label: _("Show this warning again")
							}
						],
						submit: _('Shutdown')
					}).then(
						lang.hitch(this, function(data) {
							tools.setUserPreference({uvmmShutdownSeen: data.show_again ? 'false' : 'true'});
							this._changeState('SHUTDOWN', 'shutdown', ids, items);
						})
					);
				}
			}));
		},

		_maybeChangeState: function(/*String*/ question, /*String*/ buttonLabel, /*String*/ newState, /*String*/ action, ids, items ) {
			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				form.destroyRecursive();
			};

			if (!this._grid.canExecuteOnSelection(action, items).length) {
				dialog.alert(_('The state of the selected virtual machines can not be changed'));
				return;
			}

			form = new Form({
				widgets: [{
					name: 'question',
					type: Text,
					content: '<p>' + question + '</p>'
				}],
				buttons: [{
					name: 'cancel',
					label: _('Cancel'),
					callback: _cleanup
				}, {
					name: 'submit',
					label: buttonLabel,
					callback: lang.hitch( this, function() {
						_cleanup();
						this._changeState( newState, null, ids, items );
					} )
				}],
				layout: [ 'question' ]
			});

			_dialog = new Dialog({
				title: _('%s domain', buttonLabel),
				content: form,
				'class': 'umcPopup',
				style: 'max-width: 400px;'
			});
			_dialog.show();
		},

		_changeState: function(/*String*/ newState, action, ids, items ) {
			// chain all UMCP commands
			var deferred = new Deferred();
			deferred.resolve();

			if (action !== null) {
				if (!this._grid.canExecuteOnSelection(action, items ).length) {
					dialog.alert(_('The state of the selected virtual machines can not be changed'));
					return;
				}
			}
			array.forEach(ids, function(iid, i) {
				deferred = deferred.then(lang.hitch(this, function() {
					this.updateProgress(i, ids.length);
					return tools.umcpCommand('uvmm/domain/state', {
						domainURI: iid,
						domainState: newState
					});
				}));
			}, this);

			// finish the progress bar and add error handler
			deferred = deferred.then(lang.hitch(this, function() {
				this.moduleStore.onChange();
				this.updateProgress(ids.length, ids.length);
			}), lang.hitch(this, function(error) {
				this.moduleStore.onChange();
				this.updateProgress(ids.length, ids.length);
			}));
		},

		_changeStateInstance: function(/*String*/ newState, action, ids, items ) {
			// chain all UMCP commands
			var deferred = new Deferred();
			deferred.resolve();
			var stateFailed = false;
			this.showProgress();

			array.forEach(ids, function(iid, i) {
				deferred = deferred.then(lang.hitch(this, function() {
					return tools.umcpCommand('uvmm/instance/state', {
						uri: iid,
						state: newState
					});
				}));
			}, this);

			// finish UMCP and add error handler
			deferred = deferred.then(lang.hitch(this, function() {
				this.moduleStore.onChange();
			}), lang.hitch(this, function(error) {
				this.moduleStore.onChange();
				this.hideProgress();
				stateFailed = true;
			}));

			// wait for changed instance state
			var max = 60;
			var counter = 1;
			deferred = new Deferred();
			var wait = lang.hitch(this, function() {
				tools.umcpCommand('uvmm/instance/query', {}, false).then(lang.hitch(this, function(data) {
					var items_update = array.filter(data.result, function(item) {
						return array.some(items, function(_item) {
							return item.id == _item.id;
						});
					});
					counter += 1;
					var items_update_d = {};
					array.forEach(items_update, function(item) {
						items_update_d[item.id] = item;
					} );
					var items_changed = 0;
					array.forEach(items, function(item) {
						if (item.state != items_update_d[item.id].state) {
							items_changed++;
						}
					});
					if (items_changed == ids.length) {
						this.hideProgress();
						deferred.resolve();
					}
					if (stateFailed) {
						this.hideProgress();
						deferred.resolve();
					}
					if (counter >= max) {
						this.hideProgress();
						deferred.resolve();
					}
					if (!deferred.isResolved()) {
						tools.defer(wait, 1000);
					}
					this.filter();
				}));
			});
			tools.defer(wait, 1000);
		},

		_cloneDomain: function( ids ) {
			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				form.destroyRecursive();
			};

			var _createClone = lang.hitch(this, function( name, mac_address ) {
				// send the UMCP command
				this.showProgress();
				tools.umcpCommand('uvmm/domain/clone', {
					domainURI: ids[ 0 ],
					cloneName: name,
					macAddress: mac_address
				}).then(lang.hitch(this, function() {
					this.moduleStore.onChange();
					this.hideProgress();
				}), lang.hitch(this, function(error) {
					this.moduleStore.onChange();
					this.hideProgress();
				}));
			});

			form = new Form({
				widgets: [{
					name: 'name',
					type: TextBox,
					label: _('Please enter the name for the clone:'),
					pattern: '^[^./][^/]*$',
					invalidMessage: _('A valid clone name cannot contain "/" and may not start with "." .')
				}, {
					name: 'mac_address',
					type: ComboBox,
					label: _( 'MAC addresses' ),
					staticValues: [
						{ id : 'clone', label : _( 'Inherit MAC addresses' ) },
						{ id : 'auto', label : _( 'Generate new MAC addresses' ) }
					]
				}, {
					type: Text,
					name: 'warning_ram',
					visible: false,  // FIXME
					depends: ['name'],
					content: '<p>' + _('<b>Warning:</b> Memory size exceeds currently available RAM on node. Cloning the VM may degrade the performance of the host and all other VMs.') + '</p>'
				} ],
				buttons: [{
					name: 'cancel',
					label: _('Cancel'),
					callback: _cleanup
				}, {
					name: 'submit',
					label: _('Create'),
					callback: function() {
						var nameWidget = form.getWidget('name');
						var macWidget = form.getWidget('mac_address');
						if (nameWidget.isValid()) {
							var name = nameWidget.get('value');
							_cleanup();
							_createClone( name, macWidget.get( 'value' ) );
						}
					}
				}],
				layout: [ 'name', 'mac_address' ]
			});

			_dialog = new Dialog({
				title: _('Create a clone'),
				content: form,
				'class': 'umcPopup'
			});
			_dialog.show();
		},

		openDomainPage: function(ids) {
			if (!ids.length) {
				return;
			}
			this._domainPage.load(ids[0]);
			this.selectChild(this._domainPage);
		},

		openInstancePage: function(ids) {
			if (!ids.length) {
				return;
			}
			var _instancePage = new InstancePage({
				onClose: lang.hitch(this, function() {
					this.selectChild(this._searchPage);
					this.set('title', this.defaultTitle);
					_instancePage.destroyRecursive();
				}),
				moduleWidget: this,
				addNotification: lang.hitch(this, 'addNotification'),
				addWarning: lang.hitch(this, 'addWarning')
			});
			this.own(_instancePage);
			this.addChild(_instancePage);

			_instancePage.load(ids[0]);
			this.selectChild(_instancePage);
		},

		_getGridColumns: function(type) {
			if (type == 'node') {
				return [{
					name: 'label',
					label: _('Name'),
					formatter: lang.hitch(this, 'iconFormatter')
				}, {
					name: 'cpuUsage',
					label: _('CPU usage'),
					width: 'adjust',
					formatter: lang.hitch(this, 'cpuUsageFormatter')
				}, {
					name: 'memUsed',
					label: _('Memory usage'),
					width: 'adjust',
					formatter: lang.hitch(this, 'memoryUsageFormatter')
				}];
			}

			var cell_width = has("ff") ? '80px' : '60px';

			if (type == 'instance') {
				return [{
					name: 'label',
					label: _('Name'),
					formatter: lang.hitch(this, 'iconFormatter')
				}, {
					name: 'start',
					label: _('Start'),
					width: cell_width,
					'class': 'uvmmStartColumn',
					description: _( 'Start the instance' ),
					formatter: lang.hitch(this, '_startFormatter')
				}];
			}

			// else type == 'domain'
			var domainColumns = [{
				name: 'label',
				label: _('Name'),
				formatter: lang.hitch(this, 'iconFormatter')
			}, {
				name: 'start',
				label: _('Start'),
				width: '50px',
				'class': 'uvmmStartColumn',
				description: _( 'Start the virtual machine' ),
				formatter: lang.hitch(this, '_startFormatter')
			}, {
				name: 'vnc',
				label: _('View'),
				width: cell_width,
				description: lang.hitch(this, function(item) {
					return lang.replace( _( 'Open a view to the virtual machine {label} on {nodeName}' ), item );
				}),
				formatter: lang.hitch(this, '_viewFormatter')
			}];

			var description = {
				name: 'description',
				label: _('Description'),
				formatter: lang.hitch(this, '_descriptionFormatter')
			};

			var cpuusage = {
				name: 'cpuUsage',
				label: _('CPU usage'),
				style: 'min-width: 80px;',
				width: 'adjust',
				formatter: lang.hitch(this, 'cpuUsageFormatter')
			};

			if (tools.isTrue(this._ucr['uvmm/umc/showcpuusage'])) {
				domainColumns.splice(1, 0, cpuusage);
			}

			if (this._currentWidth > this._GRID_COLUMNS_WIDTH_LIMIT) {
				domainColumns.splice(1, 0, description);
			}

			return domainColumns;
		},

		_adjustIconColumns: function(row) {
			var cells = [this._grid._grid.getCellByField('start'), this._grid._grid.getCellByField('vnc')];
			array.forEach(cells, function(cell) {
				if (!cell) {
					// currently we are probably searching for nodes
					return;
				}
				var cellId = cell.index;
				var node = query('td[idx="' + cellId + '"]', row.node)[0];
				node.style['text-align'] = 'center';
			});
		},

		_getMigrationPausedInfo: function(item) {
			if (item.reason === 2) {
				return _('This machine will be started when the migration completes.');
			} else if (item.reason === 12) {
				return _('Do not stop this machine during a postcopy migration. It will be destroyed when the migration completes.');
			}
		},

		_startFormatter: function(val, item, col) {
			if (!canStart(item) && !isPausedForMigration(item) && !isPausedForSnapshot(item)) {
				return '';
			}
			var btn;
			var call = item.type == 'instance' ? '_changeStateInstance' : '_changeState';
			var id = item[this._grid.moduleStore.idProperty];
			var _runCallback = lang.hitch(this, call, 'RUN', 'start', [id], [item]);
			var _migrationInfoCallback = lang.hitch(this, function() {
				dialog.alert(this._getMigrationPausedInfo(item));
			});
			var snapshotInfo = _('This machine is paused to create a snapshot.');
			var _snapshotInfoCallback = function() {
				dialog.alert(snapshotInfo);
			};

			if (item._univention_cache_button_start) {
				btn = item._univention_cache_button_start;
			} else {
				btn = new Button({
					label: '',
					style: 'padding: 0; display: inline; margin: 0;',
					callback: function() {
						if (isPausedForMigration(item)) {
							_migrationInfoCallback();
						} else if (isPausedForSnapshot(item)) {
							_snapshotInfoCallback();
						} else {
							_runCallback();
						}
					}
				});
				this._grid.own(btn);
				item._univention_cache_button_start = btn;
			}
			if (isPausedForMigration(item)) {
				btn.set('iconClass', 'umcHelpIcon');
				btn.set('title', this._getMigrationPausedInfo(item));
			} else if (isPausedForSnapshot(item)) {
				btn.set('iconClass', 'umcHelpIcon');
				btn.set('title', snapshotInfo);
			} else {
				btn.set('iconClass', 'umcIconPlay');
				btn.set('title', col.description);
			}
			return btn;
		},

		_viewFormatter: function(val, item, col) {
			if (!canVNC(item)) {
				return '';
			}
			if (item._univention_cache_button_vnc) {
				return item._univention_cache_button_vnc;
			}
			var id = item[this._grid.moduleStore.idProperty];
			var btn = new Button({
				label: '',
				iconClass: 'umcIconView',
				style: 'padding: 0; display: inline; margin: 0;',
				callback: lang.hitch(this, 'vncLink', [id], [item]),
				title: col.description(item)
			});
			this._grid.own(btn);
			item._univention_cache_button_vnc = btn;
			return btn;
		},

		_getGridActions: function(type) {
			if (type == 'node' || type == 'cloud') {
				return [{
					name: 'add',
					label: _( 'Create' ),
					iconClass: 'umcIconAdd',
					isMultiAction: false,
					isContextAction: false,
					callback: lang.hitch(this, 'openCreatePage' )
				}];
			}

			if (type == 'instance') {
				return [{
					name: 'edit',
					label: _( 'Edit' ),
					isStandardAction: true,
					isMultiAction: false,
					iconClass: 'umcIconEdit',
					description: _( 'Edit the configuration of the virtual machine' ),
					callback: lang.hitch(this, 'openInstancePage'),
					canExecute: function(item) {
						return !isTerminated(item);
					}
				}, {
					name: 'start',
					label: _( 'Start' ),
					iconClass: 'umcIconPlay',
					description: _( 'Start the instance' ),
					isStandardAction: true,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'RUN', 'start' ),
					canExecute: canStart
				}, {
					name: 'restart',
					label: _( 'Restart (hard)' ),
					isStandardAction: false,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'RESTART', 'restart' ),
					canExecute: function(item) {
						return isRunning(item) && isOpenStack(item);
					}
				}, {
					name: 'softrestart',
					label: _( 'Restart (soft)' ),
					isStandardAction: false,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'SOFTRESTART', 'softrestart' ),
					canExecute: function(item) {
						return isRunning(item) && isEC2(item);
					}
				}, {
					name: 'shutdown',
					label: _( 'Shutdown (soft)' ),
					isStandardAction: false,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'SHUTDOWN', 'shutdown' ),
					canExecute: function(item) {
						return isRunning(item) && isEC2(item);
					}
				}, {
					name: 'pause',
					label: _( 'Pause' ),
					isStandardAction: false,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'PAUSE', 'pause' ),
					canExecute: function(item) {
						return isRunning(item) && !isPaused(item) && isOpenStack(item);
					}
				}, {
					name: 'Suspend',
					label: _( 'Suspend' ),
					isStandardAction: false,
					isMultiAction: true,
					callback: lang.hitch(this, '_changeStateInstance', 'SUSPEND', 'suspend' ),
					canExecute: function(item) {
						return isRunning(item) && !isPaused(item) && isOpenStack(item);
					}
				}, {
					name: 'remove',
					label: _( 'Delete' ),
					isStandardAction: false,
					isMultiAction: false,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, '_removeInstance' ),
					canExecute: function(item) {
						return item.node_available && !isTerminated(item);
					}
				}, {
					name: 'add',
					label: _( 'Create' ),
					iconClass: 'umcIconAdd',
					isMultiAction: false,
					isContextAction: false,
					callback: lang.hitch(this, 'openCreatePage' )
				}];
			}

			// else type == 'domain'
			// STATES = ( 'NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED', 'PMSUSPENDED' )
			return [{
				name: 'edit',
				label: _( 'Edit' ),
				isStandardAction: true,
				isMultiAction: false,
				iconClass: 'umcIconEdit',
				description: _( 'Edit the configuration of the virtual machine' ),
				callback: lang.hitch(this, 'openDomainPage')
			}, {
				name: 'editNewTab',
				label: _( 'Edit in new tab' ),
				isStandardAction: false,
				isMultiAction: false,
				description: _('Open a new tab to edit the configuration of the virtual machine'),
				callback: lang.hitch(this, function(ids, items) {
					var props = {
						onCloseTab: lang.hitch(this, function() {
							topic.publish('/umc/tabs/focus', this);
						}),
						openDomain: ids
					};
					topic.publish('/umc/modules/open', this.moduleID, this.moduleFlavor, props);
				})
			}, {
				name: 'start',
				label: _( 'Start' ),
				iconClass: 'umcIconPlay',
				description: _( 'Start the virtual machine' ),
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, '_changeState', 'RUN', 'start' ),
				canExecute: canStart
			}, {
				name: 'snapshot',
				label: _('Create snapshot'),
				isMultiAction: false,
				isStandardAction: false,
				isContextAction: true,
				canExecute: function(item) {
					return item.node_available && !isPausedForMigration(item);
				},
				callback: lang.hitch(this, function(ids) {
					if (!ids.length) {
						return;
					}
					tools.umcpCommand("uvmm/domain/get", {
						domainURI: ids[0]
					}).then(lang.hitch(this, function(data) {
						snapshot._addSnapshot(ids[0], data.result).then(lang.hitch(this, function() {
							dialog.alert(_('Snapshot successfully created'));
						}));
					}));
				}),
			}, {
				name: 'shutdown',
				label: _('Shutdown'),
				iconClass: 'umcIconShutdown',
				description: _('Request virtual machine shutdown using ACPI'),
				isStandardAction: false,
				isMultiAction: true,
				callback: lang.hitch(this, '_shutdown'),
				canExecute: isRunning
			}, {
				name: 'stop',
				label: _( 'Stop' ),
				iconClass: 'umcIconStop',
				description: _( 'Shut off the virtual machine' ),
				isStandardAction: false,
				isMultiAction: true,
				callback: lang.hitch(this, '_maybeChangeState',
					/* question */ _('Stopping the virtual machine will turn it off without shutting down the operating system. Should the operation be continued?'),
					/* buttonLabel */ _( 'Stop' ),
					/* newState */ 'SHUTOFF',
					/* action */ 'stop'),
				canExecute: isRunning
			}, {
				name: 'pause',
				label: _( 'Pause' ),
				iconClass: 'umcIconPause',
				isStandardAction: false,
				isMultiAction: true,
				callback: lang.hitch(this, '_changeState', 'PAUSE', 'pause' ),
				canExecute: function(item) {
					return isRunning(item) && item.state != 'PAUSED';
				}
			}, {
				name: 'suspend',
				label: _( 'Suspend' ),
				// iconClass: 'umcIconPause',
				isStandardAction: false,
				isMultiAction: true,
				callback: lang.hitch(this, '_changeState', 'SUSPEND', 'suspend' ),
				canExecute: isRunning
			}, /* { FIXME: not yet fully supported
				name: 'restart',
				label: _( 'Restart' ),
				isStandardAction: false,
				isMultiAction: true,
				callback: lang.hitch(this, '_changeState', 'RESTART', 'restart' ),
				canExecute: function(item) {
					return isRunning(item);
				}
			}, */ {
				name: 'clone',
				label: _( 'Clone' ),
				isStandardAction: false,
				isMultiAction: false,
				callback: lang.hitch(this, '_cloneDomain' ),
				canExecute: function(item) {
					return item.state == 'SHUTOFF' && item.node_available;
				}
			}, {
				name: 'vnc',
				label: _( 'View' ),
				isStandardAction: true,
				isMultiAction: false,
				iconClass: 'umcIconView',
				description: _('Open a view to the virtual machine'),
				callback: lang.hitch(this, 'vncLink' ),
				canExecute: canVNC
			}, {
				name: 'migrate',
				label: _( 'Migrate' ),
				isStandardAction: false,
				isMultiAction: false,
				callback: lang.hitch(this, '_migrate' ),
				canExecute: function(item) {
					// FIXME need to find out if there are more than one node of this type
					return !isTerminated(item) && !isPausedForMigration(item);
				}
			}, {
				name: 'remove',
				label: _( 'Remove' ),
				isStandardAction: false,
				isMultiAction: false,
				iconClass: 'umcIconDelete',
				callback: lang.hitch(this, '_removeDomain' ),
				canExecute: function(item) {
					return item.state == 'SHUTOFF' && item.node_available;
				}
			}, {
				name: 'add',
				label: _( 'Create' ),
				iconClass: 'umcIconAdd',
				isMultiAction: false,
				isContextAction: false,
				callback: lang.hitch(this, 'openCreatePage' )
			}];
		},

		cpuUsageFormatter: function(id, item) {
			// summary:
			//		Formatter method for cpu usage.

			if (undefined === item.cpuUsage) {
				return '';
			}
			if (item.type === 'domain') {
				if (!isRunning(item) || isPaused(item)) {
					// only show CPU info, if the machine is running
					return '';
				}
			} else if (item.type === 'node') {
				if (!item.available) {
					return '';
				}
			}
			var percentage = Math.round(item.cpuUsage * 100);
			var progressBar = new ProgressBar({
				value: percentage + '%'
			});
			this._grid.own(progressBar);
			return progressBar;
		},

		memoryUsageFormatter: function(id, item) {
			// summary:
			//		Formatter method for memory usage.

			if (item.type == 'node') {
				// for the node, return a progressbar
				var progressBar = new ProgressBar({
					label: lang.replace('{used} / {available}', {
						used: types.prettyCapacity(item.memUsed),
						available: types.prettyCapacity(item.memPhysical)
					}),
					maximum: item.memPhysical,
					value: item.memUsed
				});
				this._grid.own(progressBar);
				return progressBar;
			}

			// else: item.type == 'domain'
			// for the domain, return a simple string
			return types.prettyCapacity(item.mem || 0);
		},

		_iconClass: function(item) {
			var iconName = 'uvmm-' + item.type;
			if (item.type == 'node' || item.type == 'cloud') {
				if (item.virtech) {
					iconName += '-' + item.virtech;
				}
				if (!item.available) {
					iconName += '-off';
				}
			}
			else if (item.type == 'domain' || item.type == 'instance') {
				if ( !item.node_available ) {
					iconName += '-off';
				} else if (this._isMigrating(item)) {
					iconName += '-migrate';
				} else if (item.state == 'RUNNING' || item.state == 'IDLE') {
					iconName += '-on';
				} else if ( item.state == 'PAUSED' || ( item.state == 'SHUTOFF' && item.suspended ) || (item.state == 'SUSPENDED')) {
					iconName += '-paused';
					if (this._hasErrorMsg(item)) {
						iconName += '-error';
					}
				} else if (item.state == 'TERMINATED') {
					iconName += '-terminated';
				} else if (item.state == 'PENDING') {
					iconName += '-pending';
				}
			}
			return iconName + '.svg';
		},

		iconFormatter: function(label, item) {
			// summary:
			//		Formatter method that adds in a given column of the search grid icons
			//		according to the object types.

			// create an HTML image that contains the icon (if we have a valid iconName)
			var html = string.substitute('<img src="${src}" height="${height}" width="${width}" style="float:left; margin-right: 5px" /><div style="${style}">${label}</div>', {
				height: '16px',
				width: '16px',
				label: label,
				src: require.toUrl(lang.replace('dijit/themes/umc/icons/scalable/{0}', [this._iconClass(item)])),
				style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
			});
			// set content after creating the object because of HTTP404: Bug #25635
			var widget = new Text({
				style: 'vertical-align: bottom;'
			});
			this._grid.own(widget);
			widget.set('content', html);

			if ( undefined !== item.state ) {
				// use _GRID_COLUMNS_WIDTH_LIMIT to decide which details should be
				// displayed inside the tooltip
				var tooltipContent;
				var tooltipData = {
					name: label,
					state: types.getDomainStateDescription( item ),
					node: item.nodeName,
					description: entities.encode(item.description).replace('\n', '<br>'),
					vnc_port: !canVNC(item) ? '' : _( 'VNC-Port: %s', item.vnc_port)
				};

				if (this._currentWidth <= this._GRID_COLUMNS_WIDTH_LIMIT) {
					tooltipContent = lang.replace( _('Name: {name}<br>State: {state}<br>Server: {node}<br>Description: {description}<br>{vnc_port}' ), tooltipData);
				} else {
					tooltipContent = lang.replace( _('State: {state}<br>Server: {node}<br>{vnc_port}' ), tooltipData);
				}

				if (this._hasErrorMsg(item)) {
					tooltipContent += '<br>';
					tooltipContent += lang.replace(_('IO error "{reason}" on device "{device}[{srcpath}]"'), item.error);
				}

				if (this._isMigrating(item)) {
					tooltipContent += '<br>';
					tooltipContent += this._getLocalizedMigrationMsg(item.migration);
				}

				var tooltip = new Tooltip({
					label: tooltipContent,
					connectId: [ widget.domNode ],
					position: [ 'after', 'below' ],
					showDelay: 0
				});
				widget.own(tooltip);

				widget.own(on(this._grid._grid, 'contextmenu', function() {
					tooltip.close();
				}));

				// enable contextmenu under tooltip
				widget.own(on(tooltip, 'show', lang.hitch(this, function() {
					if (!!this._contextCatcher && this._contextCatcher.hasOwnProperty('remove')) {
						this._contextCatcher.remove();
					}
					this._contextCatcher = on.once(document.body, 'contextmenu', lang.hitch(this, function(evt) {
						var onTooltip = array.some(evt.path, function(element) {
							return domClass.contains(element, "dijitTooltip");
						});
						if (onTooltip) {
							evt.preventDefault();
							tooltip.close();
							this._grid._grid.clearSelection();
							this._grid._grid.select(item);
							this._grid._contextMenu._openMyself(evt);
						}
					}));
					widget.own(this._contextCatcher);
				})));

				// destroy the tooltip when the widget is destroyed
				tooltip.connect( widget, 'destroy', 'destroy' );
			}

			return widget;
		},

		_descriptionFormatter: function(description, rowIndex) {
			var html = lang.replace('<div style="{style}">{description}</div>', {
				description: description,
				style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
			});
			var widget = new Text({
				title: description
			});
			this._grid.own(widget);
			widget.set('content', html);

			return widget;
		},

		_getTreeTooltip: function(item) {
			var tooltip = '';
			if (item.type == 'node' && !item.available) {
				tooltip = lang.replace( _('Connection to server {node} failed.'), {
					node: entities.encode(item.label)
				} );
			}
			if (item.type == 'cloud' && !item.available && item.last_error_message) {
				tooltip = item.last_error_message;
			}
			return tooltip;
		},

		filter: function() {
			// summary:
			//		Send a new query with the given filter options as specified in the search form
			//		and the selected server/group.

			// validate the search form
			var search_vals = this._searchForm.get('value');
			if (!this._searchForm.getWidget('type').isValid()) {
				dialog.alert(_('Please select a valid search type.'));
				return;
			}

			var nodePattern = '', domainPattern = '', type = search_vals.type;
			var tree_path = this._tree.get('path');
			var tree_item = lang.clone(tree_path).pop();

			var dropdown = this._searchForm.getWidget('type');

			// apply filter from search
			if (type == 'domain' || type == 'instance') {
				domainPattern = search_vals.pattern;

				// only search for domains of the selected node in the tree
				if (tree_item && tree_item.type == 'node' && tree_item.id) {
					nodePattern = tree_item.id;
					type = 'domain';
				}
				if (tree_item && tree_item.type == 'cloud' && tree_item.id) {
					nodePattern = tree_item.id;
					type = 'instance';
				}
			} else {
				nodePattern = search_vals.pattern;
			}

			// update grid content and columns
			this._grid.filter({
				type: type,
				domainPattern: domainPattern,
				nodePattern: nodePattern
			});
			this.updateGrid(type);

			// update tree
			if (tree_item && tree_item.type == 'node') {
				dropdown.set('value', 'domain');
				tools.umcpCommand('uvmm/node/query', {
					nodePattern: nodePattern
				}).then(lang.hitch(this, function(response) {
					this._tree.model.changes(response.result);
				}));
			} else if (tree_item && tree_item.type == 'cloud') {
				dropdown.set('value', 'instance');
				tools.umcpCommand('uvmm/cloud/query', {
					nodePattern: nodePattern
				}).then(lang.hitch(this, function(response) {
					this._tree.model.changes(response.result);
				}));
			}
			this._itemCountChangedNoteShowed = false;
		},

		updateGrid: function(type) {
			var columns = this._getGridColumns(type);
			var actions = this._getGridActions(type);
			this._grid.setColumnsAndActions(columns, actions);
		},

		showProgress: function() {
			this._progressBar.set('value', 'Infinity');
			this.standby(true, this._progressContainer);
		},

		hideProgress: function() {
			this.standby(false);
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
		},

		closeDomainPage: function() {
			// close the UVMM module
			if (this._domainPage && this._domainPage.isClosable) {
				topic.publish('/umc/tabs/close', this);
				return;
			}
		},

		onCloseTab: function() {
			// event stub
		}
	});
});
