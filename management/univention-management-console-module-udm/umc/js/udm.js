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

dojo.require("umc.modules._udm.Template");
dojo.require("umc.modules._udm.NewObjectDialog");
dojo.require("umc.modules._udm.TreeModel");
dojo.require("umc.modules._udm.DetailPage");

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
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

	// the property field that acts as unique identifier: the LDAP DN
	idProperty: '$dn$',

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the detail page for editing an UDM object
	_detailPage: null,

	// internal reference to the signal handle to umc.modules._udm.DetailPage.onClose
	_detailPageCloseHandle: null,

	// reference to a `umc.widgets.Tree` instance which is used to display the container
	// hierarchy for the UDM navigation module
	_tree: null,

	// reference to the last item in the navigation on which a context menu has been opened
	_navContextItem: null,

	// a dict of variable -> value entries for relevant UCR variables
	_ucr: null,

	// define grid columns
	_default_columns: null,

	// UDM object type name in singular and plural
	objectNameSingular: '',
	objectNamePlural: '',

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

		if ('navigation' == this.moduleFlavor) {
			// for the UDM navigation, we only query the UCR variables
			umc.tools.ucr('directory/manager/web*').then(dojo.hitch(this, function(ucr) {
				// save the ucr variables locally and also globally
				this._ucr = umc.modules._udm.ucr = ucr;
				this.renderSearchPage();
			}));
		}
		else {
			// render search page, we first need to query lists of containers/superodinates
			// in order to correctly render the search form...
			// query also necessary UCR variables for the UDM module
			(new dojo.DeferredList([
				this.umcpCommand('udm/containers'),
				this.umcpCommand('udm/superordinates'),
				umc.tools.ucr('directory/manager/web*')
			])).then(dojo.hitch(this, function(results) {
				var containers = results[0][0] ? results[0][1] : [];
				var superordinates = results[1][0] ? results[1][1] : [];
				this._ucr = umc.modules._udm.ucr = results[2][0] ? results[2][1] : {};
				this.renderSearchPage(containers.result, superordinates.result);
			}));
		}

		// check whether we need to open directly the detail page of a given object
		if (this.openObject) {
			this.createDetailPage(this.openObject.objectType, this.openObject.objectDN);
		}
	},

	renderSearchPage: function(containers, superordinates) {
		// summary:
		//		Render all GUI elements for the search formular, the grid, and the side-bar
		//		for the UDM navigation.

		// setup search page
		this._searchPage = new umc.widgets.Page({
			headerText: this.description,
			helpText: 'Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat.'
		});
		this.addChild(this._searchPage);
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Search for %s', this.objectNamePlural),
			design: 'sidebar'
		});
		this._searchPage.addChild(titlePane);

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
		}];

		// the navigation needs a slightly modified store that uses the UMCP query
		// function 'udm/nav/object/query'
		var store = this.moduleStore;
		if ('navigation' == this.moduleFlavor) {
			store = dojo.delegate(this.moduleStore, {
				storePath: 'udm/nav/object'
			});
		}

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: this._default_columns,
			moduleStore: store,
			footerCaption: dojo.hitch(this, function(nItems, nItemsTotal) {
				// generate the caption for the grid footer
				var map = {
					nSelected: nItems,
					nTotal: nItemsTotal,
					objPlural: this.objectNamePlural,
					objSingular: this.objectNameSingular
				};
				if (1 == nItemsTotal) {
					return this._('%(nSelected)d of 1 %(objSingular)s selected', map);
				}
				else if (1 < nItemsTotal) {
					return this._('%(nSelected)d of %(nTotal)d %(objPlural)s selected', map);
				}
				return this._('No %(objPlural)s could be found', map);
			})
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
		if ('navigation' == this.moduleFlavor) {
			// nothing to do :)
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
		}

		// add remaining elements of the search form
		widgets = widgets.concat([{
			type: 'ComboBox',
			name: 'objectType',
			description: this._( 'The type of the UDM object.' ),
			label: this._('Object type'),
			//value: objTypes.length ? this.moduleFlavor : undefined,
			staticValues: objTypes,
			dynamicValues: 'udm/types',
			umcpCommand: umcpCmd,
			depends: objTypeDependencies,
			onChange: dojo.hitch(this, function(newObjType) {
				// update the object property depending on the updated object type
				var newObjProperty = this._ucr['directory/manager/web/modules/' + newObjType + '/search/default'] || '';
				var objPropertyWidget = this._searchWidget._widgets.objectProperty;
				objPropertyWidget.setInitialValue(newObjProperty || undefined, false);
				var objTypeWidget = this._searchWidget._widgets.objectType;
				objTypeWidget.setInitialValue(null, false);
			})
		}, {
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Object property' ),
			dynamicValues: 'udm/properties',
			dynamicOptions: { searchable: true },
			umcpCommand: umcpCmd,
			depends: 'objectType',
			value: autoObjProperty
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
		layout[1].push('submit', 'reset');

		// generate the search widget
		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: layout,
			onSearch: dojo.hitch(this, 'filter')
		});
		titlePane.addChild(this._searchWidget);

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
				onClick: dojo.hitch(this, 'filter'),
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return umc.tools.getIconClass(item.icon || 'udm-container-cn');
				}
			});
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
					this.removeObjects(this._navContextItem.id);
				})
			}));
			menu.addChild(new dijit.MenuItem({
				label: this._( 'Reload' ),
				iconClass: 'dijitIconUndo',
				onClick: dojo.hitch(this, function() {
					this._tree.reload();
				})
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

		// hide the 'objectType' combo box in case it shows only one value
		var handle = this.connect(this._searchWidget._widgets.objectType, 'onValuesLoaded', function(values) {
			this._searchWidget._widgets.objectType.set('visible', values.length > 1);
		});

		// check whether we have autosearch activated
		if ('navigation' != this.moduleFlavor && umc.tools.isTrue(autoSearch)) {
			// connect to the onValuesInitialized event of the form
			var handle = this.connect(this._searchWidget, 'onValuesInitialized', function() {
				this.filter(this._searchWidget.gatherFormValues());
				this.disconnect(handle);
			});
		}
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
		var items = this._searchWidget._widgets.objectProperty.getAllItems();
		for ( var i in items ) {
			if ( items[ i ].identifies ) {
				return items[ i ];
			}
		}
		return null;
	},

	filter: function(vals) {
		// summary:
		//		Send a new query with the given filter options as specified in the search form
		//		and (for the UDM navigation) the selected container.

		if ('navigation' == this.moduleFlavor) {
			var items = this._tree.get('selectedItems');
			if (items.length) {
				this._grid.filter({
					container: items[0].id
				});
			}
		}
		else {
			var identifies = this.identityProperty();
			var selected_value = this._searchWidget._widgets.objectProperty.get( 'value' );
			var columns = this._default_columns;
			if ( identifies === null || selected_value != identifies.id ) {
				var new_column = {
					name: selected_value,
					label: this._searchWidget._widgets.objectProperty.get( 'displayedValue' )
				};
				columns = this._default_columns.slice( 0, 1 ).concat( new_column, this._default_columns.slice( 1 ) );
			}

			this._grid.filter(vals);
			this._grid.set( 'columns', columns );
		}
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
			onDone: dojo.hitch(this, function(options) {
				// when the options are specified, create a new detail page
				options.objectType = options.objectType || this.moduleFlavor; // default objectType is the module flavor
				this.createDetailPage(options.objectType, undefined, options);
			}),
			objectNamePlural: this.objectNamePlural,
			objectNameSingular: this.objectNameSingular
		});
	},

	createDetailPage: function(objectType, ldapName, newObjOptions) {
		// summary:
		//		Creates and views the detail page for editing UDM objects.

		this._detailPage = new umc.modules._udm.DetailPage({
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			moduleStore: this.moduleStore,
			moduleFlavor: this.moduleFlavor,
			objectType: objectType,
			ldapName: ldapName,
			newObjectOptions: newObjOptions,
			moduleWidget: this
		});
		this._detailPageCloseHandle = dojo.connect(this._detailPage, 'onClose', this, 'closeDetailPage');
		this.addChild(this._detailPage);
		this.selectChild(this._detailPage);
	},

	closeDetailPage: function() {
		// summary:
		//		Closes the detail page for editing UDM objects.

		this.resetTitle();
		this.selectChild(this._searchPage);
		if (this._detailPageCloseHandle) {
			dojo.disconnect(this._detailPageCloseHandle);
			this._detailPageCloseHandle = null;
		}
		if (this._detailPage) {
			this.removeChild(this._detailPage);
			this._detailPage.destroyRecursive();
			this._detailPage = null;
		}
	}
});



