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
/*global define require console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojo/on",
	"dojo/topic",
	"dojo/aspect",
	"dojo/json",
	"dojo/dom-class",
	"dijit/registry",
	"dijit/layout/ContentPane",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/_TextBoxMixin",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/Form",
	"umc/widgets/SearchForm",
	"umc/widgets/Button",
	"umc/widgets/Tree",
	"umc/modules/udm/TreeModel",
	"umc/modules/udm/CreateReportDialog",
	"umc/modules/udm/NewObjectDialog",
	"umc/modules/udm/DetailPage",
	"umc/i18n!umc/modules/udm",
	"umc/modules/udm/MultiObjectSelect",
	"umc/modules/udm/ComboBox",
	"umc/modules/udm/CertificateUploader"
], function(declare, lang, array, Deferred, all, on, topic, aspect, json, domClass, registry, ContentPane, Menu, MenuItem, _TextBoxMixin, Dialog, tools, dialog, store, ContainerWidget, Text, Module, Page, Grid, ExpandingTitlePane, Form, SearchForm, Button, Tree, TreeModel, CreateReportDialog, NewObjectDialog, DetailPage, _) {
	return declare("umc.modules.udm", [ Module ], {
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
		//		'superordinate' (optional).
		newObject: null,

		// the property field that acts as unique identifier: the LDAP DN
		idProperty: '$dn$',

		// internal reference to the search page
		_searchPage: null,

		// internal reference to the detail page for editing an UDM object
		_detailPage: null,

		// reference to a `umc/widgets/Tree` instance which is used to display the container
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
		_navUpButton: null,

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
				label: _( 'Name' ),
				description: _( 'Name of the UDM object.' ),
				formatter: lang.hitch(this, 'iconFormatter')
			}];

			// we only need the path column for any module except the navigation
			if ('navigation' != this.moduleFlavor) {
				this._default_columns.push({
					name: 'path',
					label: _('Path'),
					description: _( 'Path of the UDM object.' )
				});
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// set the opacity for the standby to 100%
			this.standbyOpacity = 1;

			// name for the objects in the current module
			var objNames = {
				'users/user': [ _('user'), _('users') ],
				'groups': [ _('group'), _('groups') ],
				'computers': [ _('computer'), _('computers') ],
				'networks': [ _('network object'), _('network objects') ],
				'dns': [ _('DNS object'), _('DNS objects') ],
				'dhcp': [ _('DHCP object'), _('DHCP objects') ],
				'shares/share': [ _('share'), _('shares') ],
				'shares/print': [ _('printer'), _('printers') ],
				'mail': [ _('mail object'), _('mail objects') ],
				'nagios': [ _('Nagios object'), _('Nagios objects') ],
				'policies': [ _('policy'), _('policies') ],
				'default': [ _('UDM object'), _('UDM objects') ]
			};

			// this deferred is resolved when everything has been loaded
			this._finishedDeferred = new Deferred();
			this._finishedDeferred.then(lang.hitch(this, function() {
				// finish standby
				this.standby(false);
			}));

			// get the correct entry from the lists above
			this.objectNameSingular = objNames['default'][0];
			this.objectNamePlural = objNames['default'][1];
			tools.forIn(objNames, function(ikey, ival) {
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
				this.createDetailPage(this.openObject.objectType, this.openObject.objectDN, undefined, true, this.openObject.note);
				return; // do not render the search page
			}
			if (this.newObject) {
				this.createDetailPage(this.newObject.objectType, undefined, this.newObject, true, this.newObject.note);
				return; // do not render the search page
			}

			this.standby(true);
			if ('navigation' == this.moduleFlavor) {
				// for the UDM navigation, we only query the UCR variables
				this.standby(true);
				tools.ucr( [ 'directory/manager/web*', 'ldap/base' ] ).then(lang.hitch(this, function(ucr) {
					// save the ucr variables locally and also globally
					this._ucr = lang.setObject('umc.modules.udm.ucr', ucr);
					this.renderSearchPage();
				}), lang.hitch(this, function() {
					this.standby(false);
				}));
			}
			else {
				// render search page, we first need to query lists of containers/superordinates
				// in order to correctly render the search form...
				// query also necessary UCR variables for the UDM module
				this.standby(true);
				all({
					containers: this.umcpCommand('udm/containers'),
					superordinates: this.umcpCommand('udm/superordinates'),
					reports: this.umcpCommand('udm/reports/query'),
					ucr: tools.ucr( [ 'directory/manager/web*', 'ldap/base' ] )
				}).then(lang.hitch(this, function(results) {
					this._reports = results.reports.result;
					this._ucr = lang.setObject('umc.modules.udm.ucr', results.ucr);
					this.renderSearchPage(results.containers.result, results.superordinates.result);
				}), lang.hitch(this, function() {
					this.standby(false);
				}));
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			// register onClose events
			this.on('close', lang.hitch(this, 'onCloseTab'));
		},

		_ldapDN2TreePath: function( ldapDN ) {
			var path = [];
			while ( ldapDN != this._ucr[ 'ldap/base' ] ) {
				path.unshift( ldapDN );
				ldapDN = ldapDN.slice( ldapDN.indexOf( ',' ) + 1 );
			}
			path.unshift( ldapDN );

			return path;
		},

		renderSearchPage: function(containers, superordinates) {
			// summary:
			//		Render all GUI elements for the search formular, the grid, and the side-bar
			//		for the UDM navigation.

			// setup search page
			this._searchPage = new Page({
				headerText: this.description,
				helpText: ''
			});
			var titlePane = new ExpandingTitlePane({
				title: _('Search for %s', this.objectNamePlural),
				design: 'sidebar'
			});
			this._searchPage.addChild(titlePane);

			// get the license information
			if (!tools.status('udm/licenseNote')) {
				tools.status('udm/licenseNote', true);
				this.umcpCommand('udm/license', {}, false).then(lang.hitch(this, function(data) {
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
				label: _( 'Add %s', this.objectNameSingular ),
				description: _( 'Add a new %s.', this.objectNameSingular ),
				iconClass: 'umcIconAdd',
				isContextAction: false,
				isStandardAction: true,
				callback: lang.hitch(this, 'showNewObjectDialog')
			}, {
				name: 'edit',
				label: _( 'Edit' ),
				description: _( 'Edit the %s.', this.objectNameSingular ),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, function(ids, items) {
					if (items.length == 1 && items[0].objectType) {
						this.createDetailPage(items[0].objectType, ids[0]);
					}
					else if (items.length >= 1 && items[0].objectType) {
						// make sure that all objects do have the same type
						var sameType = true;
						array.forEach(items, function(iitem) {
							sameType = sameType && iitem.objectType == items[0].objectType;
							return sameType;
						});
						if (!sameType) {
							dialog.alert(_('Only objects of the same type can be edited together'));
							return;
						}

						// everything ok, load detail page
						this.createDetailPage(items[0].objectType, ids);
					}
				})
			}, {
				name: 'editNewTab',
				label: _('Edit in new tab'),
				description: _( 'Open a new tab in order to edit the UDM-object' ),
				isMultiAction: false,
				callback: lang.hitch(this, function(ids, items) {
					var moduleProps = {
						openObject: {
							objectType: items[0].objectType,
							objectDN: ids[0]
						},
						onCloseTab: lang.hitch(this, function() {
							try {
								this.focusModule();
							}
							catch (e) { }
						})
					};
					topic.publish('/umc/modules/open', this.moduleID, this.moduleFlavor, moduleProps);
				})
			}, {
				name: 'delete',
				label: _( 'Delete' ),
				description: _( 'Deleting the selected %s.', this.objectNamePlural ),
				isStandardAction: true,
				isMultiAction: true,
				iconClass: 'umcIconDelete',
				callback: lang.hitch(this, function(ids) {
					if (ids.length) {
						var isContainer = false;
						array.some(ids, lang.hitch(this, function(id) {
							var item = this._grid.getItem(id);
							if (item.objectType.substr(0, 9) == 'container') {
								isContainer = true;
							}
							return isContainer;
						}));
						this.removeObjects(ids, isContainer);
					}
				})
			}, {
				name: 'move',
				label: _('Move to...'),
				description: _( 'Move objects to a different LDAP position.' ),
				isMultiAction: true,
				callback: lang.hitch(this, function(ids) {
					if (ids.length) {
						var isContainer = false;
						array.some(ids, lang.hitch(this, function(id) {
							var item = this._grid.getItem(id);
							if (item.objectType.substr(0, 9) == 'container') {
								isContainer = true;
							}
							return isContainer;
						}));
						this.moveObjects(ids, isContainer);
					}
				})
			}];

			// the navigation needs a slightly modified store that uses the UMCP query
			// function 'udm/nav/object/query'
			var _store = this.moduleStore;
			if ('navigation' == this.moduleFlavor) {
				_store = store(this.idProperty, 'udm/nav/object', this.moduleFlavor);
			}

			// generate the data grid
			this._grid = new Grid({
				region: 'center',
				actions: actions,
				columns: this._default_columns,
				moduleStore: _store,
				footerFormatter: lang.hitch(this, function(nItems, nItemsTotal) {
					// generate the caption for the grid footer
					var map = {
						nSelected: nItems,
						nTotal: nItemsTotal,
						objPlural: this.objectNamePlural,
						objSingular: this.objectNameSingular
					};
					if (0 === nItemsTotal) {
						return _('No %(objPlural)s could be found', map);
					}
					else if (1 == nItems) {
						return _('%(nSelected)d %(objSingular)s of %(nTotal)d selected', map);
					}
					else {
						return _('%(nSelected)d %(objPlural)s of %(nTotal)d selected', map);
					}
				}),
				defaultAction: lang.hitch( this, function( keys, items ) {
					if ( 'navigation' == this.moduleFlavor && ( this._searchForm._widgets.objectType.get( 'value' ) == '$containers$' || items[ 0 ].$childs$ === true ) ) {
						this._tree.set( 'path', this._ldapDN2TreePath( keys[ 0 ] ) );
						this.filter( this._searchForm.gatherFormValues() );
					} else if ( undefined !== this._searchForm._widgets.superordinate ) {
						var found = false;
						this._searchForm._widgets.superordinate.store.fetch( { onItem: lang.hitch( this, function( item ) {
							if ( this._searchForm._widgets.superordinate.store.getValue( item, 'id' ) == keys[ 0 ] ) {
								var handle = this._searchForm._widgets.objectPropertyValue.on('valuesLoaded', lang.hitch( this, function() {
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

			var umcpCmd = lang.hitch(this, 'umcpCommand');
			var widgets = [];
			var layout = [ [], [] ]; // layout with two rows

			// check whether we need to display containers or superordinates
			var objTypeDependencies = [];
			var objTypes = [];
			var objProperties = [];
			if ('navigation' == this.moduleFlavor) {
				// add the types 'None'  and '$containers$' to objTypes
				objTypes.push( { id: 'None', label: _( 'All types' ) } );
				objTypes.push( { id: '$containers$', label: _( 'All containers' ) } );
				objProperties.push({ id: 'None', label: _( 'Default properties' ) });
			} else if (superordinates && superordinates.length) {
				// superordinates...
				widgets.push({
					type: 'ComboBox',
					name: 'superordinate',
					description: _( 'The superordinate in which the search is carried out.' ),
					label: _('Superordinate'),
					value: superordinates[0].id || superordinates[0],
					staticValues: superordinates,
					umcpCommand: umcpCmd
				});
				layout[0].push('superordinate');
				objTypeDependencies.push('superordinate');
				objTypes.push({ id: this.moduleFlavor, label: _( 'All types' ) });
				objProperties.push({ id: 'None', label: _( 'Default properties' ) });
			}
			else if (containers && containers.length) {
				// containers...
				containers.unshift({ id: 'all', label: _( 'All containers' ) });
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					description: _( 'The container in which the query is executed.' ),
					label: _('Search in:'),
					value: containers[0].id || containers[0],
					staticValues: containers,
					umcpCommand: umcpCmd
				});
				layout[0].push('container');
				objTypes.push({ id: this.moduleFlavor, label: _( 'All types' ) });
				objProperties.push({ id: 'None', label: _( 'Default properties' ) });
			}

			// add remaining elements of the search form
			widgets = widgets.concat([{
				type: 'ComboBox',
				name: 'objectType',
				description: _( 'The type of the UDM object.' ),
				label: _('%s type', tools.capitalize(this.objectNameSingular)),
				//value: objTypes.length ? this.moduleFlavor : undefined,
				staticValues: objTypes,
				dynamicValues: 'udm/types',
				umcpCommand: umcpCmd,
				depends: objTypeDependencies,
				onChange: lang.hitch(this, function(newObjType) {
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
				description: _( 'The object property on which the query is filtered.' ),
				label: _( 'Property' ),
				staticValues: objProperties,
				dynamicValues: 'udm/properties',
				dynamicOptions: { searchable: true },
				umcpCommand: umcpCmd,
				depends: 'objectType',
				value: autoObjProperty,
				onChange: lang.hitch(this, function(newVal) {
					// get the current label of objectPropertyValue
					var widget = this._searchForm.getWidget('objectProperty');
					var label = _( 'Property value' );
					array.some(widget.getAllItems(), function(iitem) {
						if (newVal == iitem.id) {
							label = iitem.label;
							return true;
						}
					});

					// update the label of objectPropertyValue
					widget = this._searchForm.getWidget('objectPropertyValue');
					widget.set('label', label);
				})
			}, {
				type: 'MixedInput',
				name: 'objectPropertyValue',
				description: _( 'The value for the specified object property on which the query is filtered.' ),
				label: _( 'Property value' ),
				dynamicValues: 'udm/values',
				umcpCommand: umcpCmd,
				depends: [ 'objectProperty', 'objectType' ]
			}]);
			layout[0].push('objectType');
			layout[1].push('objectProperty', 'objectPropertyValue');

			// add also the buttons (specified by the search form itself) to the layout
			var buttons = [{
				name: 'submit',
				label: _('Search')
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
					callback: lang.hitch(this, function() {
						this._isAdvancedSearch = !this._isAdvancedSearch;
						this._updateSearch();
					})
				});
				layout[1].push('toggleSearch');
			}

			// generate the search widget
			this._searchForm = new SearchForm({
				region: 'top',
				widgets: widgets,
				layout: layout,
				buttons: buttons,
				onSearch: lang.hitch(this, 'filter')
			});
			titlePane.addChild(this._searchForm);

			// generate the navigation pane for the navigation module
			if ('navigation' == this.moduleFlavor) {
				this._navUpButton = this.own( new Button( {
					label: _( 'Parent container' ),
					iconClass: 'umcIconUp',
					callback: lang.hitch(this, function() {
						var path = this._tree.get( 'path' );
						var ldapDN = path[ path.length - 2 ].id;
						this._tree.set( 'path', this._ldapDN2TreePath( ldapDN ) );
						this._searchForm.getWidget('superordinate').set('value', 'None');
						// we can relaunch the search after all search form values
						// have been updated
						on.once(this._searchForm.getWidget('objectPropertyValue'), 'valuesLoaded', lang.hitch(this, function() {
							this.filter();
						}));
					})
				}))[0];

				var model = new TreeModel({
					umcpCommand: umcpCmd
				});
				this._tree = new Tree({
					//style: 'width: auto; height: auto;',
					model: model,
					persist: false,
					// customize the method getIconClass()
					getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
						return tools.getIconClass(item.icon || 'udm-container-cn');
					}
				});
				// at the first onLoad event, select the LDAP base (i.e., root) as current node
				on.once(this._tree, 'load', lang.hitch(this, function() {
					// if the tree has been loaded successfully, model.root
					// is set and we can select the root as active node
					if (this._tree.model.root) {
						this._tree.set('path', [ this._tree.model.root ]);
					}
				}));
				this.own(this._tree.watch('path', lang.hitch(this, function(attr, oldVal, newVal) {
					// register for changes of the selected item (= path)
					// only take them into account in case the tree is not reloading
					if (!this._reloadingPath) {
						this.filter();
					}
					else if (this._reloadingPath == this._path2str(this._tree.get('path'))) {
						// tree has been reloaded to its last position
						this._reloadingPath = '';
					}
					if ( this._tree.get('path').length > 1 ) {
						this._grid._toolbar.addChild( this._navUpButton, 0 );
					} else {
						this._grid._toolbar.removeChild( this._navUpButton );
					}
					this._navUpButton.set( 'visible', this._tree.get('path').length > 1 );
				})));
				var treePane = new ContentPane({
					content: this._tree,
					region: 'left',
					splitter: true,
					style: 'width: 200px;'
				});

				// add a context menu to edit/delete items
				var menu = new Menu({});
				menu.addChild(new MenuItem({
					label: _( 'Edit' ),
					iconClass: 'umcIconEdit',
					onClick: lang.hitch(this, function(e) {
						this.createDetailPage(this._navContextItem.objectType, this._navContextItem.id);
					})
				}));
				menu.addChild(new MenuItem({
					label: _( 'Delete' ),
					iconClass: 'umcIconDelete',
					onClick: lang.hitch(this, function() {
						this.removeObjects(this._navContextItem.id, true);
					})
				}));
				menu.addChild(new MenuItem({
					label: _('Move to...'),
					onClick: lang.hitch(this, function() {
						this.moveObjects([this._navContextItem.id], true);
					})
				}));
				menu.addChild(new MenuItem({
					label: _( 'Reload' ),
					iconClass: 'umcIconRefresh',
					onClick: lang.hitch(this, 'reloadTree')
				}));

				// when we right-click anywhere on the tree, make sure we open the menu
				menu.bindDomNode(this._tree.domNode);
				this.own(menu);

				// remember on which item the context menu has been opened
				this.own(aspect.after(menu, '_openMyself', lang.hitch(this, function(e) {
					if (this._tree.selectedNode) {
						this._navContextItem = this._tree.selectedNode.item;
					} else {
						console.warn('this._tree.selectedNode is null');
					}
				})));
				// in the case of changes, reload the navigation, as well (could have
				// changes referring to container objects)
				this.on('objectsaved', lang.hitch(this, function(dn, objectType) {
					var isContainer = objectType.substr(0, 9) === 'container';
					this.resetPathAndReloadTreeAndFilter(isContainer);
				}));

				titlePane.addChild(treePane);
			}

			// register to onShow as well as onFilterDone events in order on focus to the
			// input widget when the tab is changed
			this._searchPage.on('show', lang.hitch(this, '_selectInputText'));
			this._grid.on('filterDone', lang.hitch(this, '_selectInputText'));

			// register event to update hiding/showing of form fields
			this._searchForm.ready().then(lang.hitch(this,  '_updateSearch'));

			// reload the superordinates in case an object has been added, it might be a new superordinate
			if (superordinates && superordinates.length) {
				//TODO: enable this behaviour
				/*
				this.own(this.on(this.moduleStore, 'onChange', function() {
					this.umcpCommand('udm/superordinates').then(lang.hitch(this, function(data) {
						var widget = this._searchForm.getWidget('superordinate');
						if (widget) {
							var currentVals = array.map(widget.get('staticValues'), function(i) { return i.id; }).sort();
							var newVals = array.map(data.result, function(i) { return i.id; }).sort();
							if (json.stringify(currentVals) != json.stringify(newVals)) {
								widget.set('staticValues', data.result);
							}
						}
					}));
				});
				*/
			}

			// focus and select text when the objectPropertyValue has been loaded
			// at the beginning
			var propertyValueHandle = this._searchForm._widgets.objectPropertyValue.watch('value', lang.hitch(this, function() {
				propertyValueHandle.remove();
				this._finishedDeferred.then(lang.hitch(this, '_selectInputText'));
			}));
			this.own(propertyValueHandle);

			// show/hide object property filter for the navigation
			if ('navigation' == this.moduleFlavor) {
				this.own(this._searchForm._widgets.objectType.watch('value', lang.hitch(this, function(attr, oldval, val) {
					this._searchForm._widgets.objectProperty.set('visible', 'None' != val && '$containers$' != val);
					this._searchForm._widgets.objectPropertyValue.set('visible', 'None' != val && '$containers$' != val);
					this.layout();
				})));
			}

			// add an additional 'up' button when the user selected a superordinate
			// for the search scope
			if (this._searchForm.getWidget('superordinate')) {
				this.own(this._searchForm.getWidget('superordinate').watch('value', lang.hitch(this, function(attr, oldval, val) {
					if ('None' == val && this._upButton) {
						// top view, no superordinate selected -> remove the button
						this._grid._toolbar.removeChild(this._upButton);
						this._upButton.destroyRecursive();
						this._upButton = null;
					}
					if (typeof val == "string" && 'None' != val && !this._upButton) {
						var label = _('Show all superordinates');
						if ('dhcp/dhcp' == this.moduleFlavor) {
							label = _('Show all DHCP services');
						}
						else if ('dns/dns' == this.moduleFlavor) {
							label = _('Show all DNS zones');
						}

						// a superordinate has been selected and we do not have a 'up' button so far -> add the button
						this._upButton = this.own(new Button({
							label: label,
							iconClass: 'umcIconUp',
							callback: lang.hitch(this, function() {
								this._searchForm.getWidget('superordinate').set('value', 'None');

								// we can relaunch the search after all search form values
								// have been updated
								on.once(this._searchForm.getWidget('objectPropertyValue'), 'valuesLoaded', lang.hitch(this, 'filter'));
							})
						}))[0];
						this._grid._toolbar.addChild(this._upButton, 0);
					}
				})));
			}

			// check whether we have autosearch activated
			if ('navigation' != this.moduleFlavor ) {
				if ( tools.isTrue(autoSearch)) {
					// connect to the onValuesInitialized event of the form
					on.once(this._searchForm, 'valuesInitialized', lang.hitch(this, function() {
						this.filter(this._searchForm.gatherFormValues());
					}));
				}
				// create report button
				this._grid.on('filterDone', lang.hitch(this, '_checkReportButton'));
			}

			this._searchPage.startup();
			this.addChild(this._searchPage);
		},

		_selectInputText: function() {
			// focus on input widget
			var widget = this._searchForm.getWidget('objectPropertyValue');
			widget.focus();

			// select the text
			var textbox = lang.getObject('_widget.textbox', false, widget);
			if (textbox) {
				try {
					_TextBoxMixin.selectInputText(textbox);
				}
				catch (err) { }
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
					widgets.objectProperty.set('visible', true);
					//widgets.objectPropertyValue.set('visible', true);
					toggleButton.set('label', _('(Simplified options)'));
				}
				else {
					widgets.objectType.set('visible', false);
					if ('superordinate' in widgets) {
						widgets.superordinate.set('visible', false);
					}
					if ('container' in widgets) {
						widgets.container.set('visible', false);
					}
					widgets.objectProperty.set('visible', false);
					//domClass.remove(widgets.objectPropertyValue.$refLabel$.domNode, 'umcZeroHeight');
					toggleButton.set('label', _('(Advanced options)'));
				}
				this.layout();
			}

			// GUI setup is done when this method has been called for the first time
			if (!this._finishedDeferred.isFulfilled()) {
				this._finishedDeferred.resolve();
			}
		},

		_createReport: function () {
			// open the dialog
			var objects = array.map( this._grid.getAllItems(), function( item ) {
				return item.$dn$;
			} );
			var _dialog = new CreateReportDialog( {
				umcpCommand: lang.hitch( this, 'umcpCommand' ),
				moduleFlavor: this.moduleFlavor,
				objects: objects,
				reports: this._reports,
				objectNamePlural: this.objectNamePlural,
				objectNameSingular: this.objectNameSingular
			} );
			_dialog.show();
		},

		_checkReportButton: function() {
			var items = this._grid.getAllItems();

			if ( items.length && this._reports.length) {
				if ( null === this._reportButton ) {
					this._reportButton = this.own( new Button( {
						label: _( 'Create report' ),
						iconClass: 'umcIconReport',
						callback: lang.hitch( this, '_createReport' )
					} ) )[0];
					this._grid._toolbar.addChild( this._reportButton );
				}
			} else if ( null !== this._reportButton ) {
				this._grid._toolbar.removeChild( this._reportButton );
				this._reportButton.destroyRecursive();
				this._reportButton = null;
			}
		},

		moveObjects: function(ids, /*Boolean?*/ isContainer) {
			if (!ids.length) {
				return;
			}

			// default values
			isContainer = isContainer === undefined ? false : isContainer;

			// add message to container widget
			var objectName = ids.length > 1 ? this.objectNamePlural : this.objectNameSingular;
			var container = new ContainerWidget({});
			container.addChild(new Text({
				content: '<p>' + _('Please select a LDAP position to move %d selected %s to:', ids.length, objectName) + '</p>',
				style: 'width:300px;'
			}));

			// create the tree
			var model = new TreeModel({
				umcpCommand: lang.hitch(this, 'umcpCommand')
			});
			var tree = new Tree({
				model: model,
				persist: false,
				style: 'width: 300px; height: 350px',
				// customize the method getIconClass()
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return tools.getIconClass(item.icon || 'udm-container-cn');
				}
			});
			container.addChild(tree);

			// add footer message
			container.addChild(new Text({
				content: '<p>' + _('Note that moving a container can take some time.') + '</p>',
				style: 'width:300px;'
			}));
			container.startup();

			// cleanup function
			var _cleanup = function() {
				container.destroyRecursive();
			};

			// ask for confirmation
			dialog.confirm(container, [{
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}, {
				name: 'move',
				label: _('Move %s', objectName)
			}]).then(lang.hitch(this, function(response) {
				if (response != 'move') {
					_cleanup();
					return;
				}

				// check whether a LDAP position has been selected
				var path = tree.get('path');
				if (!path || !path.length) {
					dialog.alert(_('No LDAP position has been selected.'));
					_cleanup();
					return;
				}

				// prepare data array
				var params = [];
				array.forEach(ids, function(idn) {
					params.push({
						'object': idn,
						options: { container: path[path.length - 1].id }
					});
				}, this);

				// set reloading path to ldap base
				if (isContainer) {
					var ldapBase = this._tree.model.getIdentity(this._tree.model.root);
					this._reloadingPath = ldapBase;
					this._tree.set('path', [ this._tree.model.root ]);
				}

				// send UMCP command to move the objects
				this.standby(true);
				this.umcpCommand('udm/move', params).then(lang.hitch(this, function(data) {
					this.standby(false);

					// check whether everything went allright
					var allSuccess = true;
					var msg = '<p>' + _('Failed to move the following objects:') + '</p><ul>';
					array.forEach(data.result, function(iresult) {
						allSuccess = allSuccess && iresult.success;
						if (!iresult.success) {
							msg += '<li>' + iresult.$dn$ + ': ' + iresult.details + '</li>';
						}
					}, this);
					msg += '</ul>';
					if (!allSuccess) {
						dialog.alert(msg);
					}

					// clear the selected objects
					this.moduleStore.onChange();
					this.resetPathAndReloadTreeAndFilter(isContainer);
				}), lang.hitch(this, function() {
					this.standby(false);
				}));

				// cleanup
				_cleanup();
			}));
		},

		// helper function that converts a path into a string
		// store original path and reload tree
		_path2str: function(path) {
			if (!path instanceof Array) {
				return '';
			}
			return json.stringify(array.map(path, function(i) {
				return i.id;
			}));
		},

		resetPathAndReloadTreeAndFilter: function(reset) {
			if (reset) {
				this._tree.set('path', [ this._tree.model.root ]);
				this.reloadTree();
			}
			this.filter();
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
				result = lang.replace('<img src="{themeUrl}/icons/16x16/udm-{icon}.png" height="{height}" width="{width}" style="float:left; margin-right: 5px" /> {value}', {
					icon: iconName,
					height: '16px',
					width: '16px',
					value: value,
					themeUrl: require.toUrl('dijit/themes/umc')
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
			var columns = null;
			var new_column = null;
			if ('navigation' == this.moduleFlavor) {
				var path = this._tree.get('path');
				if (path.length) {
					lang.mixin(vals, {
						container: path[path.length - 1].id
					});
					this._grid.filter(vals);
				}
				new_column = {
					name: 'labelObjectType',
					label: _( 'Type' )
				};
				columns = this._default_columns.slice( 0, 1 ).concat( new_column, this._default_columns.slice( 1 ) );
				this._grid.set( 'columns', columns );
			} else {
				var identifies = this.identityProperty();
				var selected_value = this._searchForm._widgets.objectProperty.get( 'value' );
				columns = this._default_columns;
				var objTypeWidget = this._searchForm._widgets.objectType;

				if ( objTypeWidget.getNumItems() > 1 ) {
					new_column = {
						name: 'labelObjectType',
						label: _( 'Type' )
					};
					columns = this._default_columns.slice( 0, 1 ).concat( new_column, this._default_columns.slice( 1 ) );
				}
				if ( 'None' != selected_value && ( identifies === null || selected_value != identifies.id ) ) {
					new_column = {
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
			var ids = _ids instanceof Array ? _ids : (_ids ? [ _ids ] : []);

			// ignore empty array
			if (!ids.length) {
				return;
			}

			// let user confirm deletion
			var msg = _('Please confirm the removal of the %d selected %s!', ids.length, this.objectNamePlural);
			if (ids.length == 1) {
				msg = _('Please confirm the removal of the selected %s!', this.objectNameSingular);
			}

			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				form.destroyRecursive();
			};

			var _remove = lang.hitch(this, function() {
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
				array.forEach(ids, function(iid) {
					this.moduleStore.remove( iid, options );
				}, this);
				transaction.commit().then(lang.hitch(this, function(data) {

					// disable standby animation
					this.standby(false);

					// see whether all objects could be removed successfully
					var success = true;
					var message = '<p>' + _('The following object(s) could not be deleted:') + '</p><ul>';
					array.forEach(data, function(iresult) {
						if (!iresult.success) {
							success = false;
							message += '<li>' + iresult.$dn$ + ': ' + iresult.details;
						}
					}, this);
					message += '</ul>';

					// show an alert in case something went wrong
					if (!success) {
						dialog.alert(message);
					}
					this.resetPathAndReloadTreeAndFilter(isContainer);
				}), lang.hitch(this, function() {
					this.standby(false);
				}));

				// remove dialog
				_cleanup();
			});

			// build a small form with a checkbox to mark whether or not referring
			// objects are deleted, as well
			form = new Form({
				widgets: [{
					type: 'Text',
					label: '',
					name: 'text',
					content: '<p>' + msg + '</p>'
				}, {
					type: 'CheckBox',
					label: _('Delete referring objects.'),
					name: 'deleteReferring',
					value: cleanup,
					style: 'width:auto'
				}],
				buttons: [{
					name: 'submit',
					label: _('Cancel'),
					callback: _cleanup
				}, {
					name: 'remove',
					label: _('Delete'),
					callback: _remove,
					style: 'float:right'
				}]
				//layout: [ 'text', [ 'deleteReferring', 'submit' ] ]
			});

			_dialog = new Dialog({
				title: _('Delete objects'),
				content: form,
				'class': 'umcPopup'
			});
			_dialog.show();
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
					dialog.alert(_('Please select a container in the LDAP directory tree. The new object will be placed at this location.'));
					return;
				}
			}

			// open the dialog
			var superordinate = this._searchForm.getWidget('superordinate');
			var _dialog = new NewObjectDialog({
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				moduleFlavor: this.moduleFlavor,
				selectedContainer: selectedContainer,
				selectedSuperordinate: superordinate && superordinate.get('value'),
				defaultObjectType: this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/add/default'] || null,
				onDone: lang.hitch(this, function(options) {
					// when the options are specified, create a new detail page
					options.objectType = options.objectType || this.moduleFlavor; // default objectType is the module flavor
					this.createDetailPage(options.objectType, undefined, options);
				}),
				objectNamePlural: this.objectNamePlural,
				objectNameSingular: this.objectNameSingular
			});
		},

		createDetailPage: function(objectType, ldapName, newObjOptions, /*Boolean?*/ isClosable, /*String*/ note) {
			// summary:
			//		Creates and views the detail page for editing UDM objects.

			if (newObjOptions) {
				// make sure that container and superordinate are at least set to null
				newObjOptions = lang.mixin({
					container: null,
					superordinate: null
				}, newObjOptions);
			}

			this._detailPage = new DetailPage({
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				moduleStore: this.moduleStore,
				moduleFlavor: this.moduleFlavor,
				objectType: objectType,
				ldapName: ldapName,
				newObjectOptions: newObjOptions,
				moduleWidget: this,
				isClosable: isClosable,
				note: note || null,
				objectNamePlural: this.objectNamePlural,
				objectNameSingular: this.objectNameSingular
			});

			this._detailPage.on('closeTab', lang.hitch(this, 'closeDetailPage'));
			this._detailPage.on('save', lang.hitch(this, 'onObjectSaved'));
			this._detailPage.on('focusModule', lang.hitch(this, 'focusModule'));
			this.addChild(this._detailPage);
			this.selectChild(this._detailPage);
		},

		closeDetailPage: function() {
			// summary:
			//		Closes the detail page for editing UDM objects.

			// in case the detail page was "closable", we need to close the module
			if (this._detailPage && this._detailPage.isClosable) {
				topic.publish('/umc/tabs/close', this);
				return;
			}

			this.resetTitle();
			this.selectChild(this._searchPage);
			if (this._detailPage) {
				this.removeChild(this._detailPage);
				this._detailPage.destroyRecursive();
				this._detailPage = null;
			}
		},

		focusModule: function() {
			// focus this module tab
			topic.publish("/umc/tabs/focus", this);
		},

		onObjectSaved: function(dn, objectType) {
			// event stub
		},

		onCloseTab: function() {
			// event stub
		}
	});
});

