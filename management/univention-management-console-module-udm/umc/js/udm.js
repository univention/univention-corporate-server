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

dojo.declare("umc.modules.udm", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		Module for handling UDM modules

	// the property field that acts as unique identifier
	idProperty: 'ldap-dn',

	_searchPage: null,
	_detailForm: null,
	_detailTabs: null,

	_receivedObjFormData: null,
	_receivedObjOrigData: null,
	_newObjOptions: null,
	_editedObjType: null,
	_propertySubTabMap: null,
	_detailPages: null,
	_tree: null,
	_template: null,

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		if ('navigation' == this.moduleFlavor) {
			// for the UDM navigation, we do not need to query
			this._renderSearchPage();
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
				this._renderSearchPage(containers.result, superordinates.result);
			}));
		}
	},

	_iconFormatter: function(value, rowIndex) {
		// get the iconNamae
		var item = this._grid._grid.getItem(rowIndex);
		var iconName = item.objectType || '';
		iconName = iconName.replace('/', '-');
		
		// create an HTML image that contains the icon (if we have a valid iconName)
		var result = value;
		if (iconName) {
			result = dojo.string.substitute('<img src="images/icons/16x16/udm-${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${value}', {
				icon: iconName, //dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
				height: '16px',
				width: '16px',
				value: value
			});
		}
		return result;
	},

	_renderSearchPage: function(containers, superordinates) {
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
			description: this._( 'Adding a new LDAP object.' ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, 'showNewObjectDialog')
		}, {
			name: 'edit',
			label: this._( 'Edit' ),
			description: this._( 'Edit the LDAP object.' ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(ids, items) {
				if (items.length && items[0].objectType) {
					this._createDetailPage(items[0].objectType, ids[0]);
				}
			})
		}, {
			name: 'delete',
			label: this._( 'Delete' ),
			description: this._( 'Deleting the selected LDAP object.' ),
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
			description: this._( 'Name of the LDAP object.' ),
			formatter: dojo.hitch(this, '_iconFormatter')
		}, {
			name: 'path',
			label: this._('Path'),
			description: this._( 'Path of the LDAP object.' ),
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
					description: this._( 'The LDAP container in which the query is executed.' ),
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
				description: this._( 'The type of the LDAP object.' ),
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
			var model = new umc.modules.udm._TreeModel({
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

	_createDetailPage: function(objectType, ldapName) {
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
			this._renderDetailPage(properties.result, layout.result, template);
			this.showDetailPage(ldapName);
		}));
	},

	_renderDetailPage: function(_properties, _layout, _template) {
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
			this._template = new umc.modules.udm._Template({
				widgets: widgets,
				template: _template[0]
			});
		}
	},

	showDetailPage: function(ldapName) {
		this.selectChild(this._detailForm);
		if (ldapName) {
			this._detailForm.load(ldapName).then(dojo.hitch(this, function(vals) {
				this._receivedObjOrigData = vals;
				this._receivedObjFormData = this._detailForm.gatherFormValues();
			}));
		}
	},

	closeDetailPage: function() {
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

	filter: function(vals) {
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

	saveChanges: function(vals) {
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
		var transaction = this.moduleStore.transaction();
		dojo.forEach(ids, function(iid) {
			this.moduleStore.remove(iid);
		}, this);
		transaction.commit();
	},

	getAlteredValues: function() {
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

	postCreate: function() {
		// only show the objectType combobox when there are different values to choose from
		/*var objTypeWidget = this._searchWidget._widgets.objectType;
		this.connect(objTypeWidget, 'onDynamicValuesLoaded', function(values) {
			if (values.length) {
				//dojo.style(objTypeWidget.
			}
		});*/
	},

	showNewObjectDialog: function() {
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
		var dialog = new umc.modules.udm._NewObjectDialog({
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			moduleFlavor: this.moduleFlavor,
			selectedContainer: selectedContainer,
			onDone: dojo.hitch(this, function(options) {
				// when the options are specified, create a new detail page
				options.objectType = options.objectType || this.moduleFlavor; // default objectType is the module flavor
				this._newObjOptions = options;
				this._createDetailPage(options.objectType);
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

dojo.declare("umc.modules.udm._NewObjectDialog", [ dijit.Dialog, umc.i18n.Mixin ], {
	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.udm',

	ucmpCommand: umc.tools.umcpCommand,

	moduleFlavor: '',

	selectedContainer: { id: '', label: '', path: '' },

	_form: null,

	style: 'max-width: 250px;',

	postMixInProperties: function() {
		this.inherited(arguments);

		dojo.mixin(this, {
			//style: 'max-width: 450px'
			title: this._( 'New UDM-Object' )
		});
	},

	buildRendering: function() {
		this.inherited(arguments);

		if ('navigation' != this.moduleFlavor) {
			// query the necessary elements to display the add-dialog correctly
			(new dojo.DeferredList([
				this.umcpCommand('udm/types'),
				this.umcpCommand('udm/containers'),
				this.umcpCommand('udm/superordinates'),
				this.umcpCommand('udm/templates')
			])).then(dojo.hitch(this, function(results) {
				var types = results[0][0] ? results[0][1] : [];
				var containers = results[1][0] ? results[1][1] : [];
				var superordinates = results[2][0] ? results[2][1] : [];
				var templates = results[3][0] ? results[3][1] : [];
				this._renderForm(types.result, containers.result, superordinates.result, templates.result);
			}));
		}
		else {
			// for the UDM navigation, only query object types
			this.umcpCommand('udm/types').then(dojo.hitch(this, function(data) {
				this._renderForm(data.result);
			}));
		}
	},

	_renderForm: function(types, containers, superordinates, templates) {
		// default values and sort items
		types = types || [];
		containers = containers || [];
		superordinates = superordinates || [];
		templates = templates || [];
		dojo.forEach([types, containers, superordinates, templates], function(iarray) {
			iarray.sort(umc.tools.cmpObjects('label'));
		});

		
		// depending on the list we get, create a form for adding
		// a new UDM object
		var widgets = [];
		var layout = [];

		if ('navigation' != this.moduleFlavor) {
			// if we have superordinates, we don't need containers
			if (superordinates.length) {
				widgets = [{
					type: 'ComboBox',
					name: 'superordinate',
					label: 'Superordinate',
					description: this._('The corresponding superordinate for the new object.'),
					staticValues: superordinates
				}, {
					type: 'ComboBox',
					name: 'objectType',
					label: 'Object type',
					description: this._('The exact object type of the new object.'),
					umcpCommand: this.umcpCommand,
					dynamicValues: 'udm/types',
					depends: 'superordinate'
				}];
				layout = [ 'superordinate', 'objectType' ];
			}
			// no superordinates, then we need a container in any case
			else {
				widgets.push({
					type: 'ComboBox',
					name: 'container',
					label: 'Container',
					description: this._('The LDAP container in which the object shall be created.'),
					staticValues: containers
				});
				layout.push('container');

				// object types
				if (types.length) {
					widgets.push({
						type: 'ComboBox',
						name: 'objectType',
						label: 'Object type',
						description: this._('The exact object type of the new object.'),
						staticValues: types
					});
					layout.push('objectType');
				}

				// templates
				if (templates.length) {
					templates.unshift({ id: 'None', label: this._('None') });
					widgets.push({
						type: 'ComboBox',
						name: 'objectTemplate',
						label: 'Object template',
						description: this._('A template defines rules for default property values.'),
						staticValues: templates
					});
					layout.push('objectTemplate');
				}
			}
		}
		else {
			// for the navigation, we show all elements and let them query their content automatically
			widgets = [{
				type: 'HiddenInput',
				name: 'container',
				value: this.selectedContainer.id
			}, {
				type: 'ComboBox',
				name: 'objectType',
				label: 'Object type',
				description: this._('The exact object type of the new object.'),
				staticValues: types
			}, {
				type: 'ComboBox',
				name: 'objectTemplate',
				label: 'Object template',
				description: this._('A template defines rules for default property values.'),
				depends: 'objectType',
				umcpCommand: this.umcpCommand,
				dynamicValues: 'udm/templates',
				staticValues: [ { id: 'None', label: this._('None') } ]
			}];
			layout = [ 'container', 'objectType', 'objectTemplate' ];
		}

		// buttons
		var buttons = [{
			name: 'add',
			label: this._('Add new object'),
			callback: dojo.hitch(this, function() {
				this.onDone(this._form.gatherFormValues());
				this.destroyRecursive();
			})
		}, {
			name: 'close',
			label: this._('Close dialog'),
			callback: dojo.hitch(this, function() {
				this.destroyRecursive();
			})
		}];

		// now create a Form
		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			buttons: buttons
		});
		var container = new umc.widgets.ContainerWidget({});
		if ('navigation' == this.moduleFlavor) {
			container.addChild(new umc.widgets.Text({
				content: this._('<p>The object will be created in the the LDAP container:</p><p><i>%s</i></p>', this.selectedContainer.path)
			}));
		}
		container.addChild(this._form);
		this.set('content', container);
		this.show();
	},

	onDone: function(options) {
		// event stub
	}
});


dojo.declare('umc.modules.udm._TreeModel', null, {
	childrenAttr: 'children',
	umcpCommand: null,

	constructor: function(args) {
		dojo.mixin(this, args);
	},

	getRoot: function(onItem) {
		this.umcpCommand('udm/nav/container/query').then(dojo.hitch(this, function(data) {
			var results = dojo.isArray(data.result) ? data.result : [];
			if (results.length) {
				onItem(results[0]);
			}
			else {
				console.log('WARNING: No top container could be queried for LDAP navigation! Ignoring error.');
			}
		}));
	},

	getLabel: function(item) {
		return item.label;
	},

	mayHaveChildren: function(item) {
		return true;
	},

	getIdentity: function(item) {
		return item.id;
	},

	getChildren: function(parentItem, onComplete) {
		this.umcpCommand('udm/nav/container/query', { container: parentItem.id }).then(dojo.hitch(this, function(data) {
			// sort items alphabetically
			var results = dojo.isArray(data.result) ? data.result : [];
			results.sort(umc.tools.cmpObjects('label'));
			onComplete(results);
		}));
	}
});


dojo.declare('umc.modules.udm._Template', null, {
	widgets: null,

	template: null,

	_inverseReferences: null,

	_userChanges: null,

	_eventHandles: null,

	_focusedWidget: '',

	// mappings to convert umlauts and special characters to standard ones
	_umlauts: { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss', 'Á' : 'A', 'Â' : 'A', 'Ã' : 'A', 'Ä' : 'A', 'Å' : 'A', 'Æ' : 'AE', 'Ç' : 'C', 'È' : 'E', 'É' : 'E', 'Ê' : 'E', 'Ë' : 'E', 'Ì' : 'I', 'Í' : 'I', 'Î' : 'I', 'Ï' : 'I', 'Ð' : 'D', 'Ñ' : 'N', 'Ò' : 'O', 'Ó' : 'O', 'Ô' : 'O', 'Õ' : 'O', 'Ö' : 'O', 'Ù' : 'U', 'Ú' : 'U', 'Û' : 'U', 'à' : 'a', 'â' : 'a', 'á' : 'a', 'ã' : 'a', 'æ' : 'ae', 'ç' : 'c', 'è' : 'e', 'é' : 'e', 'ê' : 'e', 'ë' : 'e', 'ì' : 'i', 'í' : 'i', 'î' : 'i', 'ï' : 'i', 'ñ' : 'n', 'ò' : 'o', 'ó' : 'o', 'ô' : 'o', 'ù' : 'u', 'ú' : 'u', 'û' : 'u', 'ý' : 'y', 'ÿ' : 'y', 'Ĉ' : 'C', 'ĉ' : 'c' },

	// regular expressio for matching variables in the template, this includes 
	// following possible variants with var='Univention'
	//
	// simple: 
	//   <var>               -> 'Univention'
	// with modifiers: 
	//   <var:lower>         -> 'univention'
	//   <var:upper>         -> 'UNIVENTION'
	//   <var:umlauts,upper> -> 'UNIVENTION'
	// with pythonic index operator: 
	//   <var>[0]   -> 'U'
	//   <var>[-2]  -> 'o'
	//   <var>[0:2] -> 'Un'
	//   <var>[1:]  -> 'nivention'
	//   <var>[:3]  -> 'Uni'
	//   <var>[:-3] -> 'Univent'
	//
	_regVar: /<(\w+)(:([\w,]*))?>(\[(-?\d*)(:(-?\d*))?\])?/g,

	_getModifiers: function(modifierString, startIdx, endIdx) {
		// get the correct string modifiers (can be a list of modifiers)
		var modifierNames = dojo.isString(modifierString) ? modifierString.toLowerCase().split(',') : [''];
		var modifiers = [];
		dojo.forEach(modifierNames, function(iname) {
			switch(dojo.trim(iname)) {
			case 'lower': 
				modifiers.push(function(str) {
					return dojo.isString(str) ? str.toLowerCase() : str;
				});
				break;
			case 'upper': 
				modifiers.push(function(str) {
					return dojo.isString(str) ? str.toUpperCase() : str;
				});
				break;
			case 'umlaut':
			case 'umlauts':
				modifiers.push(dojo.hitch(this, function(str) {
					if (!dojo.isString(str)) {
						return str;
					}
					var newStr = '';
					for (var i = 0; i < str.length; ++i) {
						newStr += this._umlauts[str[i]] || str[i];
					}
					return newStr;
				}));
				break;
			default:
				// default modifier is a dummy function that does nothing
				modifiers.push(function(str) { return str; });
			}
		}, this);

		// add index operator as last modifier
		modifiers.push(function(str) {
			return str.slice(startIdx, endIdx);
		});

		// return function that applies all modifiers
		return function(str) {
			dojo.forEach(modifiers, function(imod) {
				str = imod(str);
			});
			return str;
		};
	},

	constructor: function(props) {
		// mixin the props
		dojo.mixin(this, props);

		// iterate over all template values
		// * set static values directly to the form
		// * register dynamic values to react on user input
		var updaters = [];
		umc.tools.forIn(this.template, function(ikey, ival) {
			// ignore values that do not have a widget
			if (!(ikey in this.widgets)) {
				console.log('WARNING: The property "' + ikey + '" as specified by the template does not exist. Ignoring error.');
				return true;
			}

			// object for updating the field
			var updater = {
				key: ikey,
				selfReference: this.widgets[ikey],
				templateString: dojo.clone(ival),
				references: [], // ordered list of widgets that are referenced
				modifiers: [], // ordered list of string modifiers per reference
				update: function() {
					// collect all necessary values
					var vals = [];
					dojo.forEach(this.references, function(iwidget, i) {
						vals.push(this.modifiers[i](iwidget.get('value')));
					}, this);

					// the value might be a simple string or an array of strings
					var newVal;
					if (dojo.isString(this.templateString)) {
						newVal = dojo.replace(this.templateString, vals);
					}
					else if (dojo.isArray(this.templateString)) {
						newVal = [];
						dojo.forEach(this.templateString, function(istr) {
							newVal.push(dojo.replace(istr, vals));
						});
					}

					// block onChange events (so we do not register the values as changes by
					// the user) and set the value
					//this.selfReference.set('blockOnChange', true);
					this.selfReference.set('value', newVal);
					//this.selfReference.set('blockOnChange', false);
				}
			};

			// try to match all variable references... the template value might be a string
			// or an array of strings
			var nRefs = 0;
			var tmpVals = dojo.isArray(ival) ? ival : [ival];
			dojo.forEach(tmpVals, function(jval, j) {
				var matches = jval.match(this._regVar);
				dojo.forEach(matches, function(imatch) {
					// parse the matched reference
					this._regVar.lastIndex = 0; // start matching in any case from the string beginning
					var match = this._regVar.exec(imatch);

					// we have a value with variable reference... 
					// parse the variable reference and get the correct indeces
					var refKey = match[1];
					var modifier = match[3];
					var startIdx = 0;
					var endIdx = Infinity;
					try {
						startIdx = !match[5] ? 0 : parseInt(match[5], 10);
					}
					catch (err1) { }

					// check whether the user specified an end index
					if (!match[6] && dojo.isString(match[5])) {
						// nope... index points to one single character
						endIdx = startIdx + 1;
						if (0 === endIdx) {
							// startIdx == -1
							endIdx = Infinity;
						}
					}
					else if (match[6]) {
						try {
							endIdx = !match[7] && match[7] !== '0' ? Infinity : parseInt(match[7], 10);
						}
						catch (err2) { }
					}

					// register the reference
					if (!(refKey in this.widgets)) {
						// reference does not exist
						return true;
					}
					updater.references.push(this.widgets[refKey]);

					// update the template string
					if (dojo.isArray(ival)) {
						updater.templateString[j] = updater.templateString[j].replace(imatch, '{' + nRefs + '}');
					}
					else {
						updater.templateString = updater.templateString.replace(imatch, '{' + nRefs + '}');
					}

					// register the modifier
					updater.modifiers.push(this._getModifiers(modifier, startIdx, endIdx));

					// count the matched references
					++nRefs;
				}, this);
			}, this);
			if (nRefs) {
				// we have a dynamic value with variable references
				updaters.push(updater);
			}
			else {
				// we have a static value, try to set the given key
				if (ikey in this.widgets) {
					this.widgets[ikey].set('value', ival);
				}
			}
		}, this);

		// build an inverse map to the reference... i.e., we want to know for a field
		// that is being changed, which other templated fields depend on its value
		this._inverseReferences = {};
		dojo.forEach(updaters, function(iupdater) {
			// get inverse references
			dojo.forEach(iupdater.references, function(iref) {
				// when we have the first entry for this reference, initiate with an empty dict
				if (!(iref.name in this._inverseReferences)) {
					this._inverseReferences[iref.name] = {};
				}

				// register the reference
				this._inverseReferences[iref.name][iupdater.key] = iupdater;
			}, this);

			// update field for the first time
			iupdater.update();
		}, this);

		// register user changes
		this._userChanges = {};
		this._eventHandles = [];
		umc.tools.forIn(this.widgets, function(ikey, iwidget) {
			// monitor value changes... onChange for changes made automatically and
			// onKeyUp for changes made by the user
			this._eventHandles.push(dojo.connect(iwidget, 'onKeyUp', dojo.hitch(this, 'onChange', iwidget)));
			this._eventHandles.push(dojo.connect(iwidget, 'onChange', dojo.hitch(this, 'onChange', iwidget)));
		}, this);
	},

	onChange: function(widget) {
		// register that the user has changed this field manually in case the
		// focus was on this field
		if (widget.get('focused')) {
			this._userChanges[widget.name] = true;
		}

		// see whether we can update other fields that have not been changed manually
		var references = this._inverseReferences[widget.name] || {};
		umc.tools.forIn(references, function(iRefKey, iUpdater) {
			if (!this._userChanges[iRefKey]) {
				iUpdater.update();
			}
		}, this);
	},

	destroy: function() {
		dojo.forEach(this._eventHandles, dojo.disconnect);	
	}
});





