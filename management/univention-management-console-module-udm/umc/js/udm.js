/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.udm");

dojo.require("dijit.Dialog");
dojo.require("dijit.Tree");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.TabContainer");
dojo.require("dojo.DeferredList");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Text");

dojo.require("umc.modules._udm.Template");
dojo.require("umc.modules._udm.NewObjectDialog");
dojo.require("umc.modules._udm.TreeModel");

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

	// the property field that acts as unique identifier: the LDAP DN
	idProperty: 'ldap-dn',

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the formular containing all form widgets of an UDM object
	_detailForm: null,

	// internal reference to the page containing the subtabs for object properties
	_detailTabs: null,

	// object properties as they are received from the server
	_receivedObjOrigData: null,

	// initial object properties as they are represented by the form
	_receivedObjFormData: null,

	// dict containing options for creating a new UDM object (chosen by the user 
	// in the 'add object' dialog)
	_newObjOptions: null,

	// UDM object type of the current edited object
	_editedObjType: null,

	// dict that saves which form element is displayed on which subtab
	// (used to display user input errors)
	_propertySubTabMap: null,

	// array that stores extra references to all sub tabs
	// (necessary to reset change sub tab titles [when displaying input errors])
	_detailPages: null,

	// reference to a dijit.Tree instance which is used to display the container
	// hierarchy for the UDM navigation module
	_tree: null,

	// reference to the template object in order to monitor user input changes
	_template: null,

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		if ('navigation' == this.moduleFlavor) {
			// for the UDM navigation, we do not need to query
			this.renderSearchPage();
		}
		else {
			// render search page, we first need to query lists of containers/superodinates
			// in order to correctly render the search form
			(new dojo.DeferredList([
				this.umcpCommand('udm/containers'),
				this.umcpCommand('udm/superordinates')
			])).then(dojo.hitch(this, function(results) {
				var containers = results[0][0] ? results[0][1] : [];
				var superordinates = results[1][0] ? results[1][1] : [];
				this.renderSearchPage(containers.result, superordinates.result);
			}));
		}
	},

	renderSearchPage: function(containers, superordinates) {
		// summary:
		//		Render all GUI elements for the search formular, the grid, and the side-bar
		//		for the UMD navigation.

		// setup search page
		this._searchPage = new dijit.layout.BorderContainer({
			design: 'sidebar'
		});
		this.addChild(this._searchPage);

		//
		// add data grid
		//

		// define actions
		var actions = [{
			name: 'add',
			label: this._( 'Add' ),
			description: this._( 'Adding a new UDM object.' ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, 'showNewObjectDialog')
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Edit the UDM object.' ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids, items) {
				if (items.length && items[0].objectType) {
					this.createDetailPage(items[0].objectType, ids[0]);
				}
			})
		}, {
			name: 'delete',
			label: this._( 'Delete' ),
			description: this._( 'Deleting the selected UDM object.' ),
			iconClass: 'dijitIconDelete',
			callback: dojo.hitch(this, function(ids) {
				// ignore empty selections
				if (!ids.length) {
					return;
				}

				// let user confirm deletion
				var msg = this._('Please confirm the removal of the %d selected objects!', ids.length);
				if (ids.length == 1) {
					msg = this._('Please confirm the removal of the selected object!', ids.length);
				}
				umc.app.confirm(msg, [{ 
					label: this._('Delete'),
					callback: dojo.hitch(this, 'removeObjects', ids)
				}, { 
					label: this._('Cancel'), 
					'default': true 
				}]);
			})
		}];

		// define grid columns
		var columns = [{
			name: 'name',
			label: this._( 'Name' ),
			description: this._( 'Name of the UDM object.' ),
			formatter: dojo.hitch(this, 'iconFormatter')
		}, {
			name: 'path',
			label: this._('Path'),
			description: this._( 'Path of the UDM object.' ),
			editable: true
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
			columns: columns,
			moduleStore: store
		});
		this._searchPage.addChild(this._grid);

		//
		// add search widget
		//
		
		var umcpCmd = dojo.hitch(this, 'umcpCommand');
		var widgets = [];
		var layout = [];
		
		if ('navigation' == this.moduleFlavor) {
			// for the navigation we need a different search form
			widgets = [];
			layout = [];
		}
		else {
			// check whether we need to display containers or superordinates
			var objTypeDependencies = [];
			var objTypes = [];
			if (superordinates && superordinates.length) {
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
				layout.push('superordinate');
				objTypeDependencies.push('superordinate');
			}
			else if (containers && containers.length) {
				// containers...
				containers.unshift({ id: 'all', label: this._( 'All containers' ) });
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					description: this._( 'The container in which the query is executed.' ),
					label: this._('Container'),
					value: containers[0].id || containers[0],
					staticValues: containers,
					umcpCommand: umcpCmd
				});
				layout.push('container');
				objTypes.push({ id: this.moduleFlavor, label: this._( 'All types' ) });
			}

			// add remaining elements of the search form
			widgets = widgets.concat([{
				type: 'ComboBox',
				name: 'objectType',
				description: this._( 'The type of the UDM object.' ),
				label: this._('Object type'),
				value: objTypes.length ? this.moduleFlavor : undefined,
				staticValues: objTypes,
				dynamicValues: 'udm/types',
				umcpCommand: umcpCmd,
				depends: objTypeDependencies
			}, {
				type: 'ComboBox',
				name: 'objectProperty',
				description: this._( 'The object property on which the query is filtered.' ),
				label: this._( 'Object property' ),
				dynamicValues: 'udm/properties',
				dynamicOptions: { searchable: true },
				umcpCommand: umcpCmd,
				depends: 'objectType'
			}, {
				type: 'MixedInput',
				name: 'objectPropertyValue',
				description: this._( 'The value for the specified object property on which the query is filtered.' ),
				label: this._( 'Property value' ),
				dynamicValues: 'udm/values',
				umcpCommand: umcpCmd,
				depends: [ 'objectProperty', 'objectType' ]
			}]);
			layout = layout.concat([ 'objectType', 'objectProperty', 'objectPropertyValue' ]);
		}

		// generate the search widget
		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [ layout ],
			onSearch: dojo.hitch(this, 'filter')
		});
		this._searchPage.addChild(this._searchWidget);

		// generate the navigation pane for the navigation module
		if ('navigation' == this.moduleFlavor) {
			var model = new umc.modules._udm.TreeModel({
				umcpCommand: umcpCmd
			});
			this._tree = new dijit.Tree({
				//style: 'width: auto; height: auto;',
				model: model,
				persist: false,
				// customize the method getIconClass() 
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return umc.tools.getIconClass(item.icon || 'udm-container-cn');
				}
			});
			var treePane = new dijit.layout.ContentPane({
				content: this._tree,
				region: 'left',
				splitter: true,
				style: 'width: 150px;'
			});

			// encapsulate the current layout with a new BorderContainer in order to place
			// the tree navigation pane on the left side
			//var tmpContainer = new dijit.layout.BorderContainer({});
			//tmpContainer.addChild(treePane);
			//this._searchPage.region = 'center';
			//tmpContainer.addChild(this._searchPage);
			//this._searchPage = tmpContainer;
			this._searchPage.addChild(treePane);
		}

		this._searchPage.startup();
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
			this._grid.filter(vals);
		}
	},

	createDetailPage: function(objectType, ldapName) {
		// summary:
		//		Query necessary information from the server for the object detail page
		//		and initiate the rendering process.

		// remember the objectType of the object we are going to edit
		this._editedObjType = objectType;

		// for the detail page, we first need to query property data from the server
		// for the layout of the selected object type, then we can render the page
		var params = { objectType: objectType };
		var commands = [
			this.umcpCommand('udm/properties', params),
			this.umcpCommand('udm/layout', params)
		];

		// in case an object template has been chosen, add the umcp request for the template
		var objTemplate = dojo.getObject('objectTemplate', false, this._newObjOptions);
		if (objTemplate && 'None' != objTemplate) {
			commands.push(this.umcpCommand('udm/get', [objTemplate], true, 'settings/usertemplate'));
		}

		// when the commands have been finished, create the detail page
		(new dojo.DeferredList(commands)).then(dojo.hitch(this, function(results) {
			var properties = results[0][1];
			var layout = results[1][1];
			var template = results.length > 2 ? results[2][1].result : null;
			this.renderDetailPage(properties.result, layout.result, template);
			this.showDetailPage(ldapName);
		}));
	},

	renderDetailPage: function(_properties, _layout, _template) {
		// summary:
		//		Render the form with subtabs containing all object properties that can
		//		be edited by the user.

		// create detail page
		this._detailTabs = new dijit.layout.TabContainer({
			nested: true,
			region: 'center'
		});

		// parse the widget configurations
		var properties = [];
		dojo.forEach(_properties, function(iprop) {
			if ('ComplexInput' == iprop.type) {
				// handle complex widgets
				iprop.type = 'MultiInput';
			}
			if (iprop.multivalue && 'MultiInput' != iprop.type) {
				// handle multivalue inputs
				iprop.subtypes = [{ type: iprop.type }];
				iprop.type = 'MultiInput';
			}
			properties.push(iprop);
		});

		// parse the layout configuration... we would like to group all groups of advanced 
		// settings on a special sub tab
		var advancedGroup = {
			label: this._('Advanced settings'),
			description: this._('Advanced settings'),
			layout: []
		};
		var layout = [];
		dojo.forEach(_layout, function(ilayout) {
			if (ilayout.advanced) {
				// advanced groups of settings should go into one single sub tab
				var jlayout = dojo.mixin({ open: false }, ilayout);
				advancedGroup.layout.push(jlayout);
			}
			else {
				layout.push(ilayout);
			}
		});
		// if there are advanced settings, add them to the layout
		if (advancedGroup.layout.length) {
			layout.push(advancedGroup);
		}

		// render all widgets
		var widgets = umc.tools.renderWidgets(properties);

		// render the layout for each subtab
		this._propertySubTabMap = {}; // map to remember which form element is displayed on which subtab
		this._detailPages = [];
		dojo.forEach(layout, function(ilayout) {
			// create a new page, i.e., subtab
			var subTab = new umc.widgets.Page({
				title: ilayout.label || ilayout.name //TODO: 'name' should not be necessary
			});

			// add rendered layout to subtab and register subtab
			subTab.addChild(umc.tools.renderLayout(ilayout.layout, widgets));
			this._detailTabs.addChild(subTab);

			// update _propertySubTabMap
			this._detailPages.push(subTab);
			var layoutStack = [ ilayout.layout ];
			while (layoutStack.length) {
				var ielement = layoutStack.pop();
				if (dojo.isArray(ielement)) {
					layoutStack = layoutStack.concat(ielement);
				}
				else if (dojo.isString(ielement)) {
					this._propertySubTabMap[ielement] = subTab;
				}
				else if (ielement.layout) {
					layoutStack.push(ielement.layout);
				}
			}
		}, this);
		this._detailTabs.startup();

		// setup detail page, needs to be wrapped by a form (for managing the
		// form entries) and a BorderContainer (for the footer with buttons)
		var borderLayout = new dijit.layout.BorderContainer({});
		borderLayout.addChild(this._detailTabs);

		// buttons
		var buttons = umc.tools.renderButtons([{
			name: 'submit',
			label: this._('Save changes')
		}, {
			name: 'close',
			label: 'navigation' == this.moduleFlavor ? this._('Back to navigation') : this._('Back to search'),
			callback: dojo.hitch(this, 'closeDetailPage')
		}]);
		var footer = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcNoBorder'
		});
		dojo.forEach(buttons._order, function(i) { 
			footer.addChild(i);
		});
		borderLayout.addChild(footer);

		// create the form containing the whole BorderContainer as content and add 
		// the form as new 'page'
		this._detailForm = new umc.widgets.Form({
			widgets: widgets,
			content: borderLayout,
			moduleStore: this.moduleStore,
			onSubmit: dojo.hitch(this, 'validateChanges')
		});
		this.addChild(this._detailForm);

		// in case we have a template, create a new template object that takes care
		// of updating the elements in the form
		if (_template && _template.length > 0) {
			this._template = new umc.modules._udm.Template({
				widgets: widgets,
				template: _template[0]
			});
		}
	},

	showDetailPage: function(ldapName) {
		// summary:
		//		Put the page with subtabs and object properties into the foreground.

		this.selectChild(this._detailForm);
		if (ldapName) {
			this._detailForm.load(ldapName).then(dojo.hitch(this, function(vals) {
				this._receivedObjOrigData = vals;
				this._receivedObjFormData = this._detailForm.gatherFormValues();
			}));
		}
	},

	closeDetailPage: function() {
		// summary:
		//		Close the page with subtabs and object properties and destroy widgets.

		if (this._detailForm) {
			// show the search page
			this.selectChild(this._searchPage);

			// remove the detail page in the background
			var oldDetailForm = this._detailForm;
			this._detailForm = null;
			this._detailTabs = null;
			this._newObjOptions = null;
			this._receivedObjOrigData = null;
			this._receivedObjFormData = null;
			this._editedObjType = null;
			this._propertySubTabMap = null;
			this._detailPages = null;
			if (this._template) {
				this._template.destroy();
			}
			this._template = null;
			this.closeChild(oldDetailForm);
		}
	},

	validateChanges: function(e) {
		// summary:
		//		Validate the user input through the server and save changes upon success.

		// prevent standard form submission
		e.preventDefault();

		// get all values that have been altered
		var vals = this.getAlteredValues();

		// copy dict and remove the ID
		var valsNoID = dojo.mixin({}, vals);
		delete valsNoID[this.idProperty];

		// reset changed headings
		dojo.forEach(this._detailPages, function(ipage) {
			// reset the original title (in case we altered it)
			if (ipage.$titleOrig$) {
				ipage.set('title', ipage.$titleOrig$);
				delete ipage.$titleOrig$;
			}
		});

		// before storing the values, make a syntax check of the user input on the server side
		var params = {
			objectType: this._editedObjType,
			properties: valsNoID
		};
		this.umcpCommand('udm/validate', params).then(dojo.hitch(this, function(data) {
			var validation = data.result;
			var allValid = true;
			dojo.forEach(data.result, function(iprop) {
				// make sure the form element exists
				var iwidget = this._detailForm._widgets[iprop.property];
				if (!iwidget) {
					return true;
				}

				// iprop.valid and iprop.details may be arrays for properties with 
				// multiple values... set all 'true' values to 'null' in order to reset
				// the original items validation mechanism
				var iallValid = iprop.valid;
				var ivalid = iprop.valid === true ? null : iprop.valid;
				if (dojo.isArray(ivalid)) {
					for (var i = 0; i < ivalid.length; ++i) {
						iallValid = iallValid && ivalid[i];
						ivalid[i] = ivalid[i] === true ? null : ivalid[i];
					}
				}
				allValid = allValid && iallValid;

				// check whether form element is valid
				iwidget.setValid(ivalid, iprop.details);
				if (!iallValid) {
					// mark the title of the subtab (in case we have not done it already)
					var ipage = this._propertySubTabMap[iprop.property];
					if (ipage && !ipage.$titleOrig$) {
						// store the original title
						ipage.$titleOrig$ = ipage.title;
						ipage.set('title', '<span style="color:red">' + ipage.title + ' (!)</span>');
					}
				}
			}, this);

			// if all elements are valid, save element
			if (allValid) {
				this.saveChanges(vals);
			}
		}));
	},

	saveChanges: function(vals) {
		// summary:
		//		Save the user changes for the edited object.

		var deffered = null;
		if (this._newObjOptions) {
			deffered = this.moduleStore.add(vals, this._newObjOptions);
		}
		else {
			deffered = this.moduleStore.put(vals);
		}
		deffered.then(dojo.hitch(this, function() {
			this.closeDetailPage();
		}));
	},

	removeObjects: function(ids) {
		// summary:
		//		Remove the selected UDM objects.

		var transaction = this.moduleStore.transaction();
		dojo.forEach(ids, function(iid) {
			this.moduleStore.remove(iid);
		}, this);
		transaction.commit();
	},

	getAlteredValues: function() {
		// summary:
		//		Return a list of object properties that have been altered.
		
		// get all form values and see which values are new
		var vals = this._detailForm.gatherFormValues();
		var newVals = {};
		if (this._newObjOptions) {
			// get only non-empty values
			umc.tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
				if (!(dojo.isArray(ival) && !ival.length) && ival) {
					newVals[iname] = ival;
				}
			}));
		}
		else {
			// existing object .. get only the values that changed
			umc.tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
				var oldVal = this._receivedObjFormData[iname];
				if (dojo.isArray(ival)) {
					if (dojo.toJson(ival) != dojo.toJson(oldVal)) {
						newVals[iname] = ival;
					}
				}
				// string .. ignore if empty and if it was not given before
				else {
					if (oldVal != ival) {
						newVals[iname] = ival;
					}
				}
			}));

			// set the LDAP DN
			newVals[this.idProperty] = vals[this.idProperty];
		}
		return newVals;
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
				umc.app.alert(this._('Please select a container in the navigation bar. The new object will be placed at this location.'));
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
				this._newObjOptions = options;
				this.createDetailPage(options.objectType);
			})
		});
	},

	destroy: function() {
		if (this._template) {
			this._template.destroy();
			this._template = null;
		}
	}
});



