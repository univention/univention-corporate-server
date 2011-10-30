/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.udm");

dojo.require("dijit.Menu");
dojo.require("dijit.MenuItem");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojo.DeferredList");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Tree");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.require("umc.modules._udm.Template");
dojo.require("umc.modules._udm.NewObjectDialog");
dojo.require("umc.modules._udm.CreateReportDialog");
dojo.require("umc.modules._udm.TreeModel");
dojo.require("umc.modules._udm.DetailPage");

(function() {
	dojo.setObject('umc.modules._udm.setDynamicValues', function(dict) {
		// return the list specified by the property '$name$'
		// make sure that elements do not exist twice
		var tmpMap = {};
		var list =  dojo.filter(dict[dict.$name$], function(ival) {
			if (!(ival in tmpMap)) {
				tmpMap[ival] = true;
				return true;
			}
			return false;
		});
		if ( dict.$name$ == 'dnsEntryZoneForward' ) {
			list = dojo.map( list, function( item ) {
				return umc.tools.explodeDn( item[ 0 ], true )[ 0 ];
			} );
		}
		return list;
	});
})();

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.widgets._WidgetsInWidgetsMixin, umc.i18n.Mixin ], {
	// summary:
	//		Module to interface (Univention Directory Manager) UDM objects.
	// description:
	//		This class offers a GUI interface to query and manipulate the different types
	//		of UDM objects. UDM objects have different properties and functions, however,
	//		the way they are displayed is rudimentary similar across the different types.
	//		This class is meant to be used (a) either to interface a particular UDM type
	//		(users, groups, computers, ...) or (b) to display a navigation interface which
	//		shows the container hierarchy on the left side and existing UDM objects of
	//		any type on the search list. The class' behaviour is controlled by the moduleFlavor
	//		property (which is set automatically when available modules are queried during
	//		the initialization).

	// openObject: Object?
	//		If given, the module will open upon start the detail page for editing the given
	//		object (specified by its LDAP DN). This property is expected to be a dict with
	//		the properties 'objectType' and 'objectDN' (both as strings).
	openObject: null,

	// newObject: Object?
	//		If given, the module will open upon start the detail page for editing a new
	//		object (specified by its objectType). This property is expected to be a dict with
	//		the properties 'objectType', 'container', 'objectTemplate' (optional), and 
	//		'superodinate' (optional).
	newObject: null,

	// the property field that acts as unique identifier: the LDAP DN
	idProperty: '$dn$',

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the detail page for editing an UDM object
	_detailPage: null,

	// internal reference to the signal handles of umc.modules._udm.DetailPage
	_detailPageHandles: null,

	// reference to a `umc.widgets.Tree` instance which is used to display the container
	// hierarchy for the UDM navigation module
	_tree: null,

	// internal variable that indicates that the tree is reloading
	_reloadingPath: '',

	// reference to the last item in the navigation on which a context menu has been opened
	_navContextItem: null,

	// a dict of variable -> value entries for relevant UCR variables
	_ucr: null,

	// define grid columns
	_default_columns: null,

	// button to navigate back to the list of superordinates
	_upButton: null,

	// button to generate reports
	_reportButton: null,

	// available reports
	_reports: null,
	
	// internal flag whether the advanced search is shown or not
	_isAdvancedSearch: true,

	// UDM object type name in singular and plural
	objectNameSingular: '',
	objectNamePlural: '',
	
	_finishedDeferred: null,

	constructor: function() {
		this._default_columns = [{
			name: 'name',
			label: this._( 'Name' ),
			description: this._( 'Name of the UDM object.' ),
			formatter: dojo.hitch(this, 'iconFormatter')
		}];

		// we only need the path column for any module except the navigation
		if ('navigation' != this.moduleFlavor) {
			this._default_columns.push({
				name: 'path',
				label: this._('Path'),
				description: this._( 'Path of the UDM object.' )
			});
		}
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// set the opacity for the standby to 100%
		this.standbyOpacity = 1;

		// name for the objects in the current module
		var objNames = {
			'users/user': [ this._('user'), this._('users') ],
			'groups': [ this._('group'), this._('groups') ],
			'computers': [ this._('computer'), this._('computers') ],
			'networks': [ this._('network object'), this._('network objects') ],
			'dns': [ this._('DNS object'), this._('DNS objects') ],
			'dhcp': [ this._('DHCP object'), this._('DHCP objects') ],
			'shares/share': [ this._('share'), this._('shares') ],
			'shares/print': [ this._('printer'), this._('printers') ],
			'mail': [ this._('mail object'), this._('mail objects') ],
			'nagios': [ this._('Nagios object'), this._('Nagios objects') ],
			'policies': [ this._('policy'), this._('policies') ],
			'default': [ this._('UDM object'), this._('UDM objects') ]
		};

		// this deferred is resolved when everything has been loaded
		this._finishedDeferred = new dojo.Deferred();
		this._finishedDeferred.then(dojo.hitch(this, function() {
			// finish standby animation and focus on input widget
			this.standby(false);
			this._searchForm.getWidget('objectPropertyValue').focus();
			
			// register to onShow events in order on focus to the input widget
			// when the tab is changed
			this.connect(this, 'onShow', function() {
				this._searchForm.getWidget('objectPropertyValue').focus();
			})
		}));

		// get the correct entry from the lists above
		this.objectNameSingular = objNames['default'][0];
		this.objectNamePlural = objNames['default'][1];
		umc.tools.forIn(objNames, function(ikey, ival) {
			if (this.moduleFlavor.indexOf(ikey) >= 0) {
				this.objectNameSingular = ival[0];
				this.objectNamePlural = ival[1];
				return false;
			}
		}, this);
	},

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		if ( 'users/self' == this.moduleFlavor ) {
			this.openObject = {
				objectType: this.moduleFlavor,
				objectDN: 'self'
			};
		}

		// check whether we need to open directly the detail page of a given or a new object
		if (this.openObject) {
			this.createDetailPage(this.openObject.objectType, this.openObject.objectDN, undefined, true);
			return; // do not render the search page
		}
		if (this.newObject) {
			this.createDetailPage(this.newObject.objectType, undefined, this.newObject, true);
			return; // do not render the search page
		}

		this.standby(true);
		if ('navigation' == this.moduleFlavor) {
			// for the UDM navigation, we only query the UCR variables
			umc.tools.ucr( [ 'directory/manager/web*' ] ).then(dojo.hitch(this, function(ucr) {
				// save the ucr variables locally and also globally
				this._ucr = umc.modules._udm.ucr = ucr;
				this.renderSearchPage();
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		}
		else {
			// render search page, we first need to query lists of containers/superodinates
			// in order to correctly render the search form...
			// query also necessary UCR variables for the UDM module
			(new dojo.DeferredList([
				this.umcpCommand('udm/containers'),
				this.umcpCommand('udm/superordinates'),
				this.umcpCommand('udm/reports/query'),
				umc.tools.ucr( [ 'directory/manager/web*' ] )
			])).then(dojo.hitch(this, function(results) {
				// result: [ 0 ] -> success/failure, [ 1 ] -> data
				var containers = results[0][0] ? results[0][1] : [];
				var superordinates = results[1][0] ? results[1][1] : [];
				this._reports = results[ 2 ][ 0 ] ? results[ 2 ][ 1 ].result : [];
				this._ucr = umc.modules._udm.ucr = results[3][0] ? results[3][1] : {};
				this.renderSearchPage(containers.result, superordinates.result);
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		}
	},

	renderSearchPage: function(containers, superordinates) {
		// summary:
		//		Render all GUI elements for the search formular, the grid, and the side-bar
		//		for the UDM navigation.

		// setup search page
		this._searchPage = new umc.widgets.Page({
			headerText: this.description,
			helpText: ''
		});
		this.addChild(this._searchPage);
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Search for %s', this.objectNamePlural),
			design: 'sidebar'
		});
		this._searchPage.addChild(titlePane);

		// get the license information
		if (!umc.tools.status('udm/licenseNote')) {
			umc.tools.status('udm/licenseNote', true);
			this.umcpCommand('udm/license', {}, false).then(dojo.hitch(this, function(data) {
				var msg = data.result.message;
				if (msg) {
					this._searchPage.addNote(msg);
				}
			}), function() {
				console.log('WARNING: An error occurred while verifying the license. Ignoring error.');	
			});
		}

		//
		// add data grid
		//

		// define actions
		var actions = [{
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
					},
					onClose: dojo.hitch(this, function() {
						this.focusModule();
						return true;
					})
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
		}];

		// the navigation needs a slightly modified store that uses the UMCP query
		// function 'udm/nav/object/query'
		var store = this.moduleStore;
		if ('navigation' == this.moduleFlavor) {
			store = umc.store.getModuleStore(this.idProperty, 'udm/nav/object', this.moduleFlavor);

			// we need to manually wire the onChange event of this.moduleStore
			// with the reload of the grid
			this.connect(this.moduleStore, 'onChange', 'filter');
		}

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: this._default_columns,
			moduleStore: store,
			footerFormatter: dojo.hitch(this, function(nItems, nItemsTotal) {
				// generate the caption for the grid footer
				var map = {
					nSelected: nItems,
					nTotal: nItemsTotal,
					objPlural: this.objectNamePlural,
					objSingular: this.objectNameSingular
				};
				if (0 === nItemsTotal) {
					return this._('No %(objPlural)s could be found', map);
				}
				else if (1 == nItems) {
					return this._('%(nSelected)d %(objSingular)s of %(nTotal)d selected', map);
				}
				else {
					return this._('%(nSelected)d %(objPlural)s of %(nTotal)d selected', map);
				}
			}),
			defaultAction: dojo.hitch( this, function( keys, items ) {
				if ( undefined !== this._searchForm._widgets.superordinate ) {
					var found = false;
					this._searchForm._widgets.superordinate.store.fetch( { onItem: dojo.hitch( this, function( item ) {
						if ( this._searchForm._widgets.superordinate.store.getValue( item, 'id' ) == keys[ 0 ] ) {
							var handle = this.connect( this._searchForm._widgets.objectPropertyValue, 'onValuesLoaded', dojo.hitch( this, function() {
								this.filter(this._searchForm.gatherFormValues());
								this.disconnect(handle);
							} ) );
							this._searchForm._widgets.superordinate.set( 'value', keys[ 0 ] );
							found = true;
							return false;
						}
					} ) } );
					if ( found === false ) {
						return 'edit';
					}
				} else {
					return 'edit';
				}
			} )
		});

		titlePane.addChild(this._grid);

		//
		// add search widget
		//

		// get configured search values
		var autoObjProperty = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/search/default'] ||
			this._ucr['directory/manager/web/modules/default'];
		var autoSearch = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/search/autosearch'] ||
			this._ucr['directory/manager/web/modules/autosearch'];

		var umcpCmd = dojo.hitch(this, 'umcpCommand');
		var widgets = [];
		var layout = [ [], [] ]; // layout with two rows

		// check whether we need to display containers or superordinates
		var objTypeDependencies = [];
		var objTypes = [];
		var objProperties = [];
		if ('navigation' == this.moduleFlavor) {
			// add the type 'None' to objTypeas
			objTypes.push({ id: 'None', label: this._( 'All types' ) });
			objProperties.push({ id: 'None', label: this._( 'All properties' ) });
		}
		else if (superordinates && superordinates.length) {
			// superordinates...
			widgets.push({
				type: 'ComboBox',
				name: 'superordinate',
				description: this._( 'The superordinate in which the search is carried out.' ),
				label: this._('Superordinate'),
				value: superordinates[0].id || superordinates[0],
				staticValues: superordinates,
				umcpCommand: umcpCmd
			});
			layout[0].push('superordinate');
			objTypeDependencies.push('superordinate');
			objTypes.push({ id: this.moduleFlavor, label: this._( 'All types' ) });
			objProperties.push({ id: 'None', label: this._( 'All properties' ) });
		}
		else if (containers && containers.length) {
			// containers...
			containers.unshift({ id: 'all', label: this._( 'All containers' ) });
			widgets.push({
				type: 'ComboBox',
				name: 'container',
				description: this._( 'The container in which the query is executed.' ),
				label: this._('Search in:'),
				value: containers[0].id || containers[0],
				staticValues: containers,
				umcpCommand: umcpCmd
			});
			layout[0].push('container');
			objTypes.push({ id: this.moduleFlavor, label: this._( 'All types' ) });
			objProperties.push({ id: 'None', label: this._( 'All properties' ) });
		}

		// add remaining elements of the search form
		widgets = widgets.concat([{
			type: 'ComboBox',
			name: 'objectType',
			description: this._( 'The type of the UDM object.' ),
			label: this._('%s type', umc.tools.capitalize(this.objectNameSingular)),
			//value: objTypes.length ? this.moduleFlavor : undefined,
			staticValues: objTypes,
			dynamicValues: 'udm/types',
			umcpCommand: umcpCmd,
			depends: objTypeDependencies,
			onChange: dojo.hitch(this, function(newObjType) {
				// update the object property depending on the updated object type
				var newObjProperty = this._ucr['directory/manager/web/modules/' + newObjType + '/search/default'] || '';
				var objPropertyWidget = this._searchForm._widgets.objectProperty;
				objPropertyWidget.setInitialValue(newObjProperty || undefined, false);
				var objTypeWidget = this._searchForm._widgets.objectType;
				objTypeWidget.setInitialValue(null, false);
			})
		}, {
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Property' ),
			staticValues: objProperties,
			dynamicValues: 'udm/properties',
			dynamicOptions: { searchable: true },
			umcpCommand: umcpCmd,
			depends: 'objectType',
			value: autoObjProperty,
			onChange: dojo.hitch(this, function(newVal) {
				// get the current label of objectPropertyValue
				var widget = this._searchForm.getWidget('objectProperty');
				var label = this._( 'Property value' );
				dojo.forEach(widget.getAllItems(), function(iitem) {
					if (newVal == iitem.id) {
						label = iitem.label;
						return false;
					}
				});

				// update the label of objectPropertyValue
				widget = this._searchForm.getWidget('objectPropertyValue');
				widget.set('label', label);
			})
		}, {
			type: 'MixedInput',
			name: 'objectPropertyValue',
			description: this._( 'The value for the specified object property on which the query is filtered.' ),
			label: this._( 'Property value' ),
			dynamicValues: 'udm/values',
			umcpCommand: umcpCmd,
			depends: [ 'objectProperty', 'objectType' ]
		}]);
		layout[0].push('objectType');
		layout[1].push('objectProperty', 'objectPropertyValue');

		// add also the buttons (specified by the search form itself) to the layout
		var buttons = [{
			name: 'submit',
			label: this._('Search')
		}];
		if ('navigation' == this.moduleFlavor) {
			// put the buttons in the first row for the navigation
			layout[0].push('submit');
		}
		else {
			// append the buttons to the last row otherwise
			layout[1].push('submit');

			// add an additional button to toggle between advanced and simplified search
			buttons.push({
				name: 'toggleSearch',
				label: '',  // label will be set in toggleSearch
				callback: dojo.hitch(this, function() {
					this._isAdvancedSearch = !this._isAdvancedSearch;
					this._updateSearch();
				})
			});
			layout[1].push('toggleSearch');
		}

		// generate the search widget
		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: layout,
			buttons: buttons,
			onSearch: dojo.hitch(this, 'filter')
		});
		titlePane.addChild(this._searchForm);

		// generate the navigation pane for the navigation module
		if ('navigation' == this.moduleFlavor) {
			var model = new umc.modules._udm.TreeModel({
				umcpCommand: umcpCmd
			});
			this._tree = new umc.widgets.Tree({
				//style: 'width: auto; height: auto;',
				model: model,
				persist: false,
				// customize the method getIconClass()
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return umc.tools.getIconClass(item.icon || 'udm-container-cn');
				}
			});
			// at the first onLoad event, select the LDAP base (i.e., root) as current node
			var handle = this.connect(this._tree, 'onLoad', function() {
				this.disconnect(handle);
				// if the tree has been loaded successfully, model.root
				// is set and we can select the root as active node
				if (this._tree.model.root) {
					this._tree.set('path', [ this._tree.model.root ]);
				}
			});
			this._tree.watch('path', dojo.hitch(this, function() {
				// register for changes of the selected item (= path)
				// only take them into account in case the tree is not reloading
				if (!this._reloadingPath) {
					this.filter();
				}
				else if (this._reloadingPath == this._path2str(this._tree.get('path'))) {
					// tree has been reloaded to its last position
					this._reloadingPath = '';
				}
			})); 	
			// in the case of changes, reload the navigation, as well (could have 
			// changes referring to container objects)
			this.connect(this.moduleStore, 'onChange', dojo.hitch(this, 'reloadTree'));
			var treePane = new dijit.layout.ContentPane({
				content: this._tree,
				region: 'left',
				splitter: true,
				style: 'width: 200px;'
			});

			// add a context menu to edit/delete items
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
					this.removeObjects(this._navContextItem.id, true);
				})
			}));
			menu.addChild(new dijit.MenuItem({
				label: this._( 'Reload' ),
				iconClass: 'dijitIconUndo',
				onClick: dojo.hitch(this, 'reloadTree')
			}));

			// when we right-click anywhere on the tree, make sure we open the menu
			menu.bindDomNode(this._tree.domNode);

			// remember on which item the context menu has been opened
			this.connect(menu, '_openMyself', function(e) {
				var el = dijit.getEnclosingWidget(e.target);
				if (el) {
					this._navContextItem = el.item;
				}
			});

			// encapsulate the current layout with a new BorderContainer in order to place
			// the tree navigation pane on the left side
			//var tmpContainer = new dijit.layout.BorderContainer({});
			//tmpContainer.addChild(treePane);
			//this._searchPage.region = 'center';
			//tmpContainer.addChild(this._searchPage);
			//this._searchPage = tmpContainer;
			titlePane.addChild(treePane);
		}

		this._searchPage.startup();

		var objTypeWidget = this._searchForm._widgets.objectType;
		this.connect(objTypeWidget, 'onValuesLoaded', '_updateSearch');

		// hide the 'objectPropertyValue' combo box in case 'all properties' are shown
		this.connect(this._searchForm._widgets.objectProperty, 'onChange', '_updateObjectPropertyValue');

		// show/hide object property filter for the navigation
		if ('navigation' == this.moduleFlavor) {
			this.connect(this._searchForm._widgets.objectType, 'onChange', function(val) {
				this._searchForm._widgets.objectProperty.set('visible', 'None' != val);
				this._searchForm._widgets.objectPropertyValue.set('visible', 'None' != val);
				this.layout();
			});
		}

		// add an additional 'up' button when the user selected a superordinate
		// for the search scope
		if (this._searchForm.getWidget('superordinate')) {
			this.connect(this._searchForm.getWidget('superordinate'), 'onChange', function(val) {
				if ('None' == val && this._upButton) {
					// top view, no superordinate selected -> remove the button
					this._grid._toolbar.removeChild(this._upButton);
					this.orphan(this._upButton, true);
					this._upButton = null;
				}
				if (dojo.isString(val) && 'None' != val && !this._upButton) {
					var label = this._('Show all superordinates');
					if ('dhcp/dhcp' == this.moduleFlavor) {
						label = this._('Show all DHCP services');
					}
					else if ('dns/dns' == this.moduleFlavor) {
						label = this._('Show all DNS zones');
					}

					// a superordinate has been selected and we do not have a 'up' button so far -> add the button
					this._upButton = this.adopt(umc.widgets.Button, {
						label: label,
						iconClass: 'umcIconUp',
						callback: dojo.hitch(this, function() {
							this._searchForm.getWidget('superordinate').set('value', 'None');

							// we can relaunch the search after all search form values
							// have been updated
							var watchHandle = this.connect(this._searchForm.getWidget('objectPropertyValue'), 'onValuesLoaded', function() {
								this.filter();
								this.disconnect(watchHandle);
							});
						})
					});
					this._grid._toolbar.addChild(this._upButton, 0);
				}
			});
		}

		// check whether we have autosearch activated
		if ('navigation' != this.moduleFlavor ) {
			if ( umc.tools.isTrue(autoSearch)) {
				// connect to the onValuesInitialized event of the form
				var initHandle = this.connect(this._searchForm, 'onValuesInitialized', function() {
					this.filter(this._searchForm.gatherFormValues());
					this.disconnect(initHandle);
				});
			}
			// create report button
			this.connect( this._grid, 'onFilterDone', 'checkReportButton' );
		}
	},

	_updateObjectPropertyValue: function(_newVal) {
		var objPropWidget = this._searchForm._widgets.objectProperty;
		var objPropValWidget = this._searchForm._widgets.objectPropertyValue;
		var labelWidget = objPropValWidget.$refLabel$;
		//var newVal = _newVal === undefined ? objPropWidget.get('value') : _newVal;
		var newVal = objPropWidget.get('value');
		if ('None' == newVal) {
			//if (this._isAdvancedSearch) {
			//	// we can hide the widget
			//	objPropValWidget.set('visible', false);
			//}
			//else {
				// we need to set the height to 0 in order not to affect the position
				// of the buttons... $refLabel$ is the reference to the Label widget
				dojo.addClass(labelWidget.domNode, 'umcZeroHeight');
			//}
		}
		else {
			// restore the height and show widget
			//objPropValWidget.set('visible', true);
			dojo.removeClass(labelWidget.domNode, 'umcZeroHeight');
		}
	},

	_updateSearch: function() {
		if ('navigation' != this.moduleFlavor) {
			var widgets = this._searchForm._widgets;
			var toggleButton = this._searchForm._buttons.toggleSearch;
			if (!this._isAdvancedSearch) {
				widgets.objectType.set('visible', widgets.objectType.getAllItems().length > 2);
				if ('superordinate' in widgets) {
					widgets.superordinate.set('visible', true);
				}
				if ('container' in widgets) {
					widgets.container.set('visible', true);
				}
				//widgets.objectProperty.set('visible', true);
				//widgets.objectPropertyValue.set('visible', true);
				toggleButton.set('label', this._('(Simplified options)'));
			}
			else {
				widgets.objectType.set('visible', false);
				if ('superordinate' in widgets) {
					widgets.superordinate.set('visible', false);
				}
				if ('container' in widgets) {
					widgets.container.set('visible', false);
				}
				//widgets.objectProperty.set('visible', false);
				//dojo.removeClass(widgets.objectPropertyValue.$refLabel$.domNode, 'umcZeroHeight');
				toggleButton.set('label', this._('(Advanced options)'));
			}
			this._updateObjectPropertyValue();
			this.layout();
		}

		// GUI setup is done when this method has been called for the first time
		if (this._finishedDeferred.fired < 0) {
			this._finishedDeferred.resolve();
		}
	},

	createReport: function ( objects ) {
		// open the dialog
		var dialog = new umc.modules._udm.CreateReportDialog( {
			umcpCommand: dojo.hitch( this, 'umcpCommand' ),
			moduleFlavor: this.moduleFlavor,
			objects: objects,
			reports: this._reports,
			objectNamePlural: this.objectNamePlural,
			objectNameSingular: this.objectNameSingular
		} );
		dialog.show();
	},

	checkReportButton: function() {
		var items = this._grid.getAllItems();

		if ( items.length && this._reports.length) {
			if ( null === this._reportButton ) {
				this._reportButton = this.adopt( umc.widgets.Button, {
					label: this._( 'Create report' ),
					iconClass: 'dijitIconDocuments', // FIXME: we need a new icon
					callback: dojo.hitch( this, 'createReport', dojo.map( items, function( item ) { return item.$dn$; } ) )
				} );
				this._grid._toolbar.addChild( this._reportButton );
			}
		} else if ( null !== this._reportButton ) {
			this._grid._toolbar.removeChild( this._reportButton );
			this.orphan( this._reportButton, true );
			this._reportButton = null;
		}
	},

	// helper function that converts a path into a string
	// store original path and reload tree
	_path2str: function(path) {
		if (!dojo.isArray(path)) {
			return '';
		}
		return dojo.toJson(dojo.map(path, function(i) {
			return i.id;
		}));
	},

	reloadTree: function() {
		// set the internal variable that indicates whether the tree is reloading
		// or not to 'false' as soon as the tree has been reloaded
		this._reloadingPath = this._path2str(this._tree.get('path'));
		this._tree.reload();
	},

	iconFormatter: function(value, rowIndex) {
		// summary:
		//		Formatter method that adds in a given column of the search grid icons
		//		according to the object types.

		// get the iconNamae
		var item = this._grid._grid.getItem(rowIndex);
		var iconName = item.objectType || '';
		iconName = iconName.replace('/', '-');

		// create an HTML image that contains the icon (if we have a valid iconName)
		var result = value;
		if (iconName) {
			result = dojo.string.substitute('<img src="images/icons/16x16/udm-${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${value}', {
				icon: iconName,
				height: '16px',
				width: '16px',
				value: value
			});
		}
		return result;
	},

	identityProperty: function() {
		var items = this._searchForm._widgets.objectProperty.getAllItems();
		for ( var i in items ) {
			if ( items[ i ].identifies ) {
				return items[ i ];
			}
		}
		return null;
	},

	filter: function() {
		// summary:
		//		Send a new query with the given filter options as specified in the search form
		//		and (for the UDM navigation) the selected container.

		var vals = this._searchForm.gatherFormValues();
		if ('navigation' == this.moduleFlavor) {
			var path = this._tree.get('path');
			if (path.length) {
				dojo.mixin(vals, {
					container: path[path.length - 1].id
				});
				this._grid.filter(vals);
			}
		}
		else {
			var identifies = this.identityProperty();
			var selected_value = this._searchForm._widgets.objectProperty.get( 'value' );
			var columns = this._default_columns;
			if ( 'None' != selected_value && ( identifies === null || selected_value != identifies.id ) ) {
				var new_column = {
					name: selected_value,
					label: this._searchForm._widgets.objectProperty.get( 'displayedValue' )
				};
				columns = this._default_columns.slice( 0, 1 ).concat( new_column, this._default_columns.slice( 1 ) );
			}

			this._grid.filter(vals);
			this._grid.set( 'columns', columns );
		}
	},

	removeObjects: function( /*String|String[]*/ _ids, /*Boolean?*/ isContainer, /*Boolean?*/ cleanup, /*Boolean?*/ recursive ) {
		// summary:
		//		Remove the selected UDM objects.

		// default values
		isContainer = isContainer === undefined ? false : isContainer;
		cleanup = cleanup === undefined ? true : cleanup;
		recursive = undefined === recursive ? true : recursive;

		// get an object
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

		// build a small form with a checkbox to mark whether or not referring 
		// objects are deleted, as well
		var widgets = [{
			type: 'CheckBox',
			label: this._('Delete referring objects.'),
			name: 'deleteReferring',
			value: cleanup
		}, {
			type: 'Text',
			label: '',
			name: 'text',
			content: msg
		}];
		var layout = [ 'text', 'deleteReferring' ];
		var form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			buttons: []
		});

		// show the confirmation dialog
		umc.dialog.confirm(form, [{
			label: this._('Delete'),
			callback: dojo.hitch(this, function() {
				// enable standby animation
				this.standby(true);

				// set reloading path to ldap base
				if (isContainer) {
					var ldapBase = this._tree.model.getIdentity(this._tree.model.root);
					this._reloadingPath = ldapBase;
					this._tree.set('path', [ this._tree.model.root ]);
				}

				// set the options
				var options = {
					cleanup: form.getWidget('deleteReferring').get('value'),
					recursive: recursive
				};

				// remove the selected elements via a transaction on the module store
				var transaction = this.moduleStore.transaction();
				dojo.forEach(ids, function(iid) {
					this.moduleStore.remove( iid, options );
				}, this);
				transaction.commit().then(dojo.hitch(this, function(data) {

					// disable standby animation
					this.standby(false);

					// see whether all objects could be removed successfully
					var success = true;
					var message = '<p>' + this._('The following object(s) could not be deleted:') + '</p><ul>';
					dojo.forEach(data.result, function(iresult) {
						if (!iresult.success) {
							success = false;
							message += '<li>' + iresult.$dn$ + ': ' + iresult.details;
						}
					}, this);
					message += '</ul>';

					// show an alert in case something went wrong
					if (!success) {
						umc.dialog.alert(message);
					}
				}), dojo.hitch(this, function() {
					this.standby(false);
				}));
			})
		}, {
			label: this._('Cancel'),
			'default': true
		}]);

	},

	showNewObjectDialog: function() {
		// summary:
		//		Open a user dialog for creating a new UDM object.

		// when we are in navigation mode, make sure the user has selected a container
		var selectedContainer = { id: '', label: '', path: '' };
		if ('navigation' == this.moduleFlavor) {
			var items = this._tree.get('selectedItems');
			if (items.length) {
				selectedContainer = items[0];
			}
			else {
				umc.dialog.alert(this._('Please select a container in the navigation bar. The new object will be placed at this location.'));
				return;
			}
		}

		// open the dialog
		var dialog = new umc.modules._udm.NewObjectDialog({
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			moduleFlavor: this.moduleFlavor,
			selectedContainer: selectedContainer,
			defaultObjectType: this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/add/default'] || null,
			onDone: dojo.hitch(this, function(options) {
				// when the options are specified, create a new detail page
				options.objectType = options.objectType || this.moduleFlavor; // default objectType is the module flavor
				this.createDetailPage(options.objectType, undefined, options);
			}),
			objectNamePlural: this.objectNamePlural,
			objectNameSingular: this.objectNameSingular
		});
	},

	createDetailPage: function(objectType, ldapName, newObjOptions, /*Boolean?*/ isClosable) {
		// summary:
		//		Creates and views the detail page for editing UDM objects.

		if (newObjOptions) {
			// make sure that container and superordinate are at least set to null
			newObjOptions = dojo.mixin({
				container: null,
				superordinate: null
			}, newObjOptions);
		}

		this._detailPage = new umc.modules._udm.DetailPage({
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			moduleStore: this.moduleStore,
			moduleFlavor: this.moduleFlavor,
			objectType: objectType,
			ldapName: ldapName,
			newObjectOptions: newObjOptions,
			moduleWidget: this,
			isClosable: isClosable
		});
		this._detailPageHandles = [];

		this._detailPageHandles.push(this.connect(this._detailPage, 'onClose', 'closeDetailPage'));
		this._detailPageHandles.push(this.connect(this._detailPage, 'onSave', 'onObjectSaved'));
		this._detailPageHandles.push(this.connect(this._detailPage, 'onFocusModule', 'focusModule'));
		this.addChild(this._detailPage);
		this.selectChild(this._detailPage);
	},

	closeDetailPage: function() {
		// summary:
		//		Closes the detail page for editing UDM objects.

		// in case the detail page was "closable", we need to close the module
		if (this._detailPage && this._detailPage.isClosable) {
			dojo.publish('/umc/tabs/close', [ this ]);
			return;
		}

		this.resetTitle();
		this.selectChild(this._searchPage);
		if (this._detailPageHandles) {
			dojo.forEach(this._detailPageHandles, dojo.hitch(this, 'disconnect'));
			this._detailPageHandles = null;
		}
		if (this._detailPage) {
			this.removeChild(this._detailPage);
			this._detailPage.destroyRecursive();
			this._detailPage = null;
		}
	},

	focusModule: function() {
		// focus this module tab
		dojo.publish("/umc/tabs/focus", [ this ]); 
	},

	onObjectSaved: function(dn, objectType) {
		// event stub
	}
});



