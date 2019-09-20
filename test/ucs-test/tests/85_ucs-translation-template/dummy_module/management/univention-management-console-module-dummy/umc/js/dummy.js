/*
 * Copyright 2016-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"umc/dialog",
	"umc/widgets/Grid",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/Module",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/modules/dummy/DetailPage",
	"umc/i18n!umc/modules/dummy"
], function(declare, lang, on, dialog, Grid, Page, SearchForm, Module, TextBox, ComboBox, DetailPage, _) {
	return declare("umc.modules.dummy", [ Module ], {
		// summary:
		//		Template module to ease the UMC module development.
		// description:
		//		This module is a template module in order to aid the development of
		//		new modules for Univention Management Console.

		// the property field that acts as unique identifier for the object
		idProperty: 'id',

		// internal reference to the grid
		_grid: null,

		// internal reference to the search page
		_searchPage: null,

		// internal reference to the detail page for editing an object
		_detailPage: null,

		// Set the opacity for the standby animation to 100% in order to mask
		// GUI changes when the module is opened. Call this.standby(true|false)
		// to enabled/disable the animation.
		standbyOpacity: 1,

		postMixInProperties: function() {
			// is called after all inherited properties/methods have been mixed
			// into the object (originates from dijit._Widget)

			// it is important to call the parent's postMixInProperties() method
			this.inherited(arguments);
		},

		buildRendering: function() {
			// is called after all DOM nodes have been setup
			// (originates from dijit._Widget)

			// it is important to call the parent's postMixInProperties() method
			this.inherited(arguments);

			// start the standby animation in order prevent any interaction before the
			// form values are loaded
			this.standby(true);

			// render the page containing search form and grid

			// setup search page and its main widgets
			// for the styling, we need a title pane surrounding search form and grid
			this._searchPage = new Page({
				headerText: this.description,
				helpText: ''
			});

			// umc.widgets.Module is also a StackContainer instance that can hold
			// different pages (see also umc.widgets.TabbedModule)
			this.addChild(this._searchPage);

			//
			// data grid
			//

			// define grid actions
			var actions = [{
				name: 'add',
				label: _('Add object'),
				description: _('Create a new object'),
				iconClass: 'umcIconAdd',
				isContextAction: false,
				isStandardAction: true,
				callback: lang.hitch(this, '_addObject')
			}, {
				name: 'edit',
				label: _('Edit'),
				description: _('Edit the selected object'),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, '_editObject')
			}, {
				name: 'delete',
				label: _('Delete'),
				description: _('Deleting the selected objects.'),
				isStandardAction: true,
				isMultiAction: true,
				iconClass: 'umcIconDelete',
				callback: lang.hitch(this, '_deleteObjects')
			}];

			// define the grid columns
			var columns = [{
				name: 'name',
				label: _('Name'),
				width: '60%'
			}, {
				name: 'color',
				label: _('Favorite color'),
				width: '40%'
			}];

			// generate the data grid
			this._grid = new Grid({
				// property that defines the widget's position
				region: 'main',
				actions: actions,
				// defines which data fields are displayed in the grids columns
				columns: columns,
				// a generic UMCP module store object is automatically provided
				// as this.moduleStore (see also store.getModuleStore())
				moduleStore: this.moduleStore,
				// initial query
				query: { colors: 'None', name: '' }
			});

			//
			// search form
			//

			// add remaining elements of the search form
			var widgets = [{
				type: ComboBox,
				name: 'color',
				description: _('Defines the .'),
				label: _('Category'),
				// Values are dynamically loaded from the server via a UMCP request.
				// Use the property dynamicOptions to pass additional values to the server.
				// Use staticValues to pass an array directly (see umc.widgets._SelectMixin).
				dynamicValues: 'dummy/colors'
			}, {
				type: TextBox,
				name: 'name',
				description: _('Specifies the substring pattern which is searched for in the displayed name'),
				label: _('Search pattern')
			}];

			// the layout is an 2D array that defines the organization of the form elements...
			// here we arrange the form elements in one row and add the 'submit' button
			var layout = [
				[ 'color', 'name', 'submit' ]
			];

			// generate the search form
			this._searchForm = new SearchForm({
				// property that defines the widget's position in a dijit.layout.BorderContainer
				region: 'nav',
				widgets: widgets,
				layout: layout,
				onSearch: lang.hitch(this, function(values) {
					// call the grid's filter function
					// (could be also done via on() and dojo.disconnect() )
					this._grid.filter(values);
				})
			});

			// turn off the standby animation as soon as all form values have been loaded
			on.once(this._searchForm, 'valuesInitialized', lang.hitch(this, function() {
				this.standby(false);
			}));

			// add search form and grid to the search page
			this._searchPage.addChild(this._searchForm);
			this._searchPage.addChild(this._grid);


			//
			// conclusion
			//

			// we need to call page's startup method manually as all widgets have
			// been added to the page container object
			this._searchPage.startup();

			// create a DetailPage instance
			this._detailPage = new DetailPage({
				moduleStore: this.moduleStore
			});
			this.addChild(this._detailPage);

			// connect to the onClose event of the detail page... we need to manage
			// visibility of sub pages here
			// ... widget.on() will destroy signal handlers upon widget
			// destruction automatically
			this._detailPage.on('close', lang.hitch(this, function() {
				this.selectChild(this._searchPage);
			}));
		},

		_addObject: function() {
			dialog.alert(_('Feature not yet implemented'));
		},

		_editObject: function(ids, items) {
			if (ids.length != 1) {
				// should not happen
				return;
			}

			this.selectChild(this._detailPage);
			this._detailPage.load(ids[0]);
		},

		_deleteObjects: function(ids, items) {
			dialog.alert(_('Feature not yet implemented'));
		}
	});
});
