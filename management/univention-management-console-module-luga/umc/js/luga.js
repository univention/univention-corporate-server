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

define([
	"umc.dialog",
	"umc.i18n",
	"umc.widgets.ExpandingTitlePane",
	"umc.widgets.Grid",
	"umc.widgets.Module",
	"umc.widgets.Page",
	"umc.widgets.SearchForm",
	"umc.modules._luga.DetailPage"
], function(dialog, i18n, ExpandingTitlePane, Grid, Module, Page, SearchForm, DetailPage) {

	var luga = {};

	return {
//dojo.declare("umc.modules.luga", [ umc.widgets.Module, umc.i18n.Mixin ], {

		// internal reference to the module store
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
			this.inherited(arguments);

			// define the idProperty
			this.idProperty = this.moduleFlavor === 'users' ? 'username' : 'groupname';

			// determine objecttype with help of flavor
			var objNames = {
				'users': [ this._('user'), this._('users') ],
				'groups': [ this._('group'), this._('groups') ]
			};

			this.objectNameSingular = objNames[this.moduleFlavor][0];
			this.objectNamePlural = objNames[this.moduleFlavor][1];

			// create the module store
			this.moduleStore = umc.store.getModuleStore(this.idProperty, 'luga/' + this.moduleFlavor, this.moduleFlavor);

			// Set the opacity for the standby animation to 100% in order to mask
			// GUI changes when the module is opened. Call this.standby(true|false)
			// to enabled/disable the animation.
			this.standbyOpacity = 1;
		},

		buildRendering: function() {
			this.inherited(arguments);
			// render the page containing search form and grid
			this.renderSearchPage();
		},

		renderSearchPage: function(containers, superordinates) {
			// render all GUI elements for the search formular and the grid

			// setup search page and its main widgets
			this._searchPage = new Page({
				headerText: this.description,
				helpText: ''
			});

			this.addChild(this._searchPage);

			var titlePane = new ExpandingTitlePane({
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
			if (this.moduleFlavor === 'users') {
				columns = [{
					name: 'username',
					label: this._('Username'),
					width: '35%'
				}, {
					name: 'fullname',
					label: this._('Fullname'),
					width: '50%'
				}, {
					name: 'lock',
					label: this._('Account'),
					width: 'adjust',
					formatter: dojo.hitch(this, function(value) {
						return value ? this._('enabled') : this._('disabled');
					})
				}, {
					name: 'pw_is_expired',
					label: this._('Password'),
					width: 'adjust',
					formatter: dojo.hitch(this, function(value) {
						return value ? this._('expired') : this._('not expired');
					})
				}];
			}
			else if (this.moduleFlavor === 'groups') {
				columns = [{
					name: 'groupname',
					label: this._('Groupname'),
					width: '100%'
				}];
			}

			// generate the data grid
			this._grid = new Grid({
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
			if (this.moduleFlavor === 'groups') {
				staticValues = [
					{id: 'groupname', label: this._('Groupname')},
					{id: 'gid', label: this._('Group ID')},
					{id: 'users', label: this._('Users')}
				];
			} else if (this.moduleFlavor === 'users') {
				staticValues = [
					{id: 'username', label: this._('Username')},
					{id: 'group', label: this._('Group membership')},
					{id: 'fullname', label: this._('Fullname')},
					{id: 'uid', label: this._('User ID')},
					{id: 'gid', label: this._('Group ID')},
					{id: 'gecos', label: this._('Additional information')},
					{id: 'homedir', label: this._('Home directory')},
					{id: 'shell', label: this._('Login shell')}
				];
			}

			// add remaining elements of the search form
			var widgets = [{
				type: 'ComboBox',
				name: 'category',
				description: this._('Defines the category'),
				label: this._('Category'),
				staticValues: staticValues
			}, {
				type: 'TextBox',
				name: 'pattern',
				description: this._('Specifies the substring pattern which is searched for in the selected category'),
				value: '*',
				label: this._('Search pattern')
			}];

			// the layout is an 2D array that defines the organization of the form elements...
			// here we arrange the form elements in one row and add the 'submit' button
			var layout = [
				[ 'category', 'pattern', 'submit' ]
			];

			// generate the search form
			this._searchForm = new SearchForm({
				// property that defines the widget's position in a dijit.layout.BorderContainer
				region: 'top',
				widgets: widgets,
				layout: layout,
				onSearch: dojo.hitch(this, function(values) {
					// call the grid's filter function
					this._grid.filter(values);
				})
			});

			// add search form to the title pane
			titlePane.addChild(this._searchForm);

			//
			// conclusion
			//

			// we need to call page's startup method manually as all widgets have
			// been added to the page container object
			this._searchPage.startup();

			// create a DetailPage instance
			this._detailPage = new DetailPage({
				moduleFlavor: this.moduleFlavor,
				moduleStore: this.moduleStore,
				objectNameSingular: this.objectNameSingular,
				objectNamePlural: this.objectNamePlural
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
			this._detailPage.load();
		},

		_editObject: function(ids, items) {
			if (ids.length == 1) {
				this.selectChild(this._detailPage);
				this._detailPage.load(ids[0]);
			}
		},

		_getDeleteUserForm: function() {
			var widgets = [{
				type: 'CheckBox',
				name: 'force',
				checked: false,
				label: this._('Force removal of files, even if not owned by user')
			}, {
				type: 'CheckBox',
				name: 'remove',
				checked: true,
				label: this._('Remove home directory and mail spool')
			}];

			var form = new umc.widgets.Form({
				widgets: widgets
			});
			return form;
		},

		showErrors: function(result) {
			this.standby(false);
			if(result && result.length) {
				var message = this._('The following errors occured while deleting the selected %s:', this._objectNamePlural) + '<ul>';
				if(dojo.isArray(result)) {
					dojo.forEach(result, function(err) {
						if (!err.success) {
							message += '<li>' + err.message + '</li>';
						}
					}, this);
				} else {
					message += '<li>' + result + '</li>';
				}
				message += '</ul>';
				dialog.alert(message);
			}
		},

		_deleteObjects: function(ids, items) {

			var form;
			var textWidget = new umc.widgets.ContainerWidget();

			textWidget.addChild(new umc.widgets.Text().set('content', this._('Please confirm removing the selected %s(s): %s', this.objectNameSingular, ids.join(', '))));

			if (this.moduleFlavor === 'users') {
				form = this._getDeleteUserForm();
				textWidget.addChild(form);
			}

			dialog.confirm(textWidget, [{
				label: this._('OK'),
				callback: dojo.hitch(this, function() {
					var options = null;
					if (this.moduleFlavor === 'users') {
						options = {
							force: form.getWidget('force').get('value'),
							remove: form.getWidget('remove').get('value')
						};
					}
					var transaction = this.moduleStore.transaction();
					dojo.forEach(ids, dojo.hitch(this, function(id) {
						this.moduleStore.remove(id, options);
					}));
					transaction.commit().then(this.showErrors, dojo.hitch(this, function() {
						this.standby(false);
					}));
				})
			}, {
				label: this._('Cancel'),
				"default": true
			}]);
		}
	}
});

