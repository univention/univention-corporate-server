/*
 * Copyright 2012 Univention GmbH
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
/*global console dojo dojox dijit umc */

dojo.provide("umc.modules.luga");

dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");

dojo.require("umc.modules._luga.DetailPage");

dojo.declare("umc.modules.luga", [ umc.widgets.Module, umc.i18n.Mixin ], {
	// summary:
	//		
	// description:
	//		
	//		
	
	moduleStore: null,

	// the property field that acts as unique identifier for the object
	idProperty: null,

	// internal reference to the grid
	_grid: null,

	// internal reference to the search page
	_searchPage: null,

	// internal reference to the detail page for editing an object
	_detailPage: null,

	// object type name in singular and plural
	objectNameSingular: null,
	objectNamePlural: null,

	postMixInProperties: function() {
		// is called after all inherited properties/methods have been mixed
		// into the object (originates from dijit._Widget)

		// it is important to call the parent's postMixInProperties() method
		this.inherited(arguments);

		this.idProperty = this.moduleFlavor === 'luga/users' ? 'username' : 'groupname';

		var objNames = {
			'luga/users': [ this._('user'), this._('users') ],
			'luga/groups': [ this._('group'), this._('groups') ]
		};

		this.objectNameSingular = objNames[this.moduleFlavor][0];
		this.objectNamePlural = objNames[this.moduleFlavor][1];

		if (this.idProperty) {
			this.moduleStore = umc.store.getModuleStore(this.idProperty, this.moduleFlavor, this.moduleFlavor);
		}

		// Set the opacity for the standby animation to 100% in order to mask
		// GUI changes when the module is opened. Call this.standby(true|false)
		// to enabled/disable the animation.
		this.standbyOpacity = 1;
	},

	buildRendering: function() {
		// is called after all DOM nodes have been setup
		// (originates from dijit._Widget)

		// it is important to call the parent's postMixInProperties() method
		this.inherited(arguments);

		// start the standby animation in order prevent any interaction before the
		// form values are loaded
	//	this.standby(true); // FIXME

		// render the page containing search form and grid
		this.renderSearchPage();
	},

	renderSearchPage: function(containers, superordinates) {
		// render all GUI elements for the search formular and the grid

		// setup search page and its main widgets
		// for the styling, we need a title pane surrounding search form and grid
		this._searchPage = new umc.widgets.Page({
			headerText: this.description,
			helpText: ''
		});

		// umc.widgets.Module is also a StackContainer instance that can hold
		// different pages (see also umc.widgets.TabbedModule)
		this.addChild(this._searchPage);

		// umc.widgets.ExpandingTitlePane is an extension of dijit.layout.BorderContainer
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Search results')
		});
		this._searchPage.addChild(titlePane);


		//
		// data grid
		//

		// define grid actions
		var actions = [{
			name: 'add',
			label: this._('Add %s', this.objectNameSingular),
			description: this._('Create a new %s', this.objectNameSingular),
			iconClass: 'umcIconAdd',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, '_addObject')
		}, {
			name: 'edit',
			label: this._('Edit'),
			description: this._('Edit the selected %s', this.objectNameSingular),
			iconClass: 'umcIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, '_editObject')
		}, {
			name: 'delete',
			label: this._('Delete'),
			description: this._('Deleting the selected %s.', this.objectNamePlural),
			isStandardAction: true,
			isMultiAction: true,
			iconClass: 'umcIconDelete',
			callback: dojo.hitch(this, '_deleteObjects')
		}];

		// define the grid columns
		var columns = null;
		if (this.moduleFlavor === 'luga/users') {
			columns = [{
				name: 'lock',
				label: this._('Enabled'),
				width: 'adjust',
				formatter: function(value) {
					return value ? '&#10799;' : '&#10004;';
				}
			}, {
				name: 'username',
				label: this._('Username'),
				width: '52%'
			}, {
				name: 'fullname',
				label: this._('Fullname'),
				width: '40%'
			}];
		}
		else if (this.moduleFlavor === 'luga/groups') {
			columns = [{
				name: 'groupname',
				label: this._('Groupname'),
				width: '100%'
			}];
		}

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			// initial query
			query: { 
				category: '',
				pattern: '*'
			}
		});

		// add the grid to the title pane
		titlePane.addChild(this._grid);


		//
		// search form
		//
		var staticValues = null;
		if (this.moduleFlavor === 'luga/groups') {
			staticValues = [
				{id: 'groupname', label: this._('Groupname')},
				{id: 'gid', label: this._('GID')},
				{id: 'users', label: this._('Users')},
				{id: 'administrators', label: this._('Administrators')}
			];
		} else if (this.moduleFlavor === 'luga/users') {
			staticValues = [
				{id: 'username', label: this._('Username')},
				{id: 'group', label: this._('Group membership')},
				{id: 'uid', label: this._('User ID')},
				{id: 'gid', label: this._('Group ID')},
				{id: 'gecos', label: this._('Additional Information')},
				{id: 'homedir', label: this._('Home directory')},
				{id: 'shell', label: this._('Login shell')}
			];
		}

		// add remaining elements of the search form
		var widgets = [{
			type: 'ComboBox',
			name: 'category',
			description: this._('Defines the .'),
			label: this._('Category'),
			staticValues: staticValues
		}, {
			type: 'TextBox',
			name: 'pattern',
			description: this._('Specifies the substring pattern which is searched for in the displayed name'),
			value: '*',
			label: this._('Search pattern')
		}];

		// the layout is an 2D array that defines the organization of the form elements...
		// here we arrange the form elements in one row and add the 'submit' button
		var layout = [
			[ 'category', 'pattern', 'submit' ]
		];

		// generate the search form
		this._searchForm = new umc.widgets.SearchForm({
			// property that defines the widget's position in a dijit.layout.BorderContainer
			region: 'top',
			widgets: widgets,
			layout: layout,
			onSearch: dojo.hitch(this, function(values) {
				// call the grid's filter function
				this._grid.filter(values);
			})
		});

		// turn off the standby animation as soon as all form values have been loaded
	//	this.connect(this._searchForm, 'onValuesInitialized', function() {
	//		this.standby(false);
	//	});

		// add search form to the title pane
		titlePane.addChild(this._searchForm);

		//
		// conclusion
		//

		// we need to call page's startup method manually as all widgets have
		// been added to the page container object
		this._searchPage.startup();

		// create a DetailPage instance
		this._detailPage = new umc.modules._luga.DetailPage({
			moduleFlavor: this.moduleFlavor,
			moduleStore: this.moduleStore
		});
		this.addChild(this._detailPage);

		// connect to the onClose event of the detail page... we need to manage
		// visibility of sub pages here
		this.connect(this._detailPage, 'onClose', function() {
			this.selectChild(this._searchPage);
		});
	},

	_addObject: function() {
		this.selectChild(this._detailPage);
		this._detailPage.add();
	},

	_editObject: function(ids, items) {
		if (ids.length == 1) {
			this.selectChild(this._detailPage);
			this._detailPage.load(ids[0]);
		}
	},

	_deleteObjects: function(ids, items) {
		if (this.moduleFlavor === 'luga/users') {
			this._deleteUsers(ids, items);
		}
		else if (this.moduleFlavor === 'luga/groups') {
			this._deleteGroups(ids, items);
		}
	},

	_addGroup: function() {},
	_deleteGroups: function(ids) {
		var confirm_message = '';
		if (ids.length == 1) {
			confirm_message = this._('Please confirm removing the selected group: %s', ids[0]);
		}
		else {
			confirm_message = this._('Please confirm removing the selected groups: %s', ids.join(', '));
		}
		umc.dialog.confirm(confirm_message, [{
			label: this._('Ok'),
			callback: dojo.hitch(this, function(ids) {
				this.moduleStore.remove(ids);
			})
		}, {
				label: this._('Cancel')
		}]);
	},

	_addUser: function() {},
	_deleteUsers: function(usernames, userobjects) {
		// TODO: ask for -r -f
		var msg = '';
//		if(usernames.length == 1) {
			msg = this._('Please confirm removing the selected user(s) %s!', usernames.join(', '));
//		} else {
//			msg = this._('Please confirm removing the selected users: %s!', ...);
//		}

		umc.dialog.confirm(msg, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
			})
		}, {
			label: this._('Cancel')
		}]);
	}

});



