/*
 * Copyright 2014 Univention GmbH
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

define([
	'dojo/_base/declare',
	'dojo/_base/lang',
	'dojo/on',
	'umc/dialog',
	'umc/tools',
	'umc/widgets/Grid',
	'umc/widgets/Page',
	'umc/widgets/SearchForm',
	'umc/widgets/ExpandingTitlePane',
	'umc/widgets/Module',
	'umc/widgets/TextBox',
	'umc/widgets/ComboBox',
	'umc/modules/supphealth/DetailPage',
	'umc/i18n!umc/modules/supphealth'
], function(declare, lang, on, dialog, tools, Grid, Page, SearchForm, ExpandingTitlePane, Module, TextBox, ComboBox, DetailPage, _) {
	return declare('umc.modules.supphealth',  Module, {
		// name of the property which is used as id for grid entries
		idProperty: 'pluginFileName',

		// references to child widgets
		_grid: null,
		_overviewPage: null,
		_detailPage: null,

		/* formatting functions as used by grid 
		(also passed to DetailPage in order to keep a consistent format) */
		timestampFormatter: function(value) {
			if(value == null)
				return _('Never');
			return value;
		},

		summaryFormatter: function(value) {
			if(value == null)
				return _('-----');
			return value;
		},

		resultFormatter: function(value) {
			if(value == '0')
				return '<span style="color:green">' + _('Successful') + '</span>';
			else if(value == '1')
				return '<span style="color:orange">' + _('Problems detected') + '</span>';
			else if(value == '-1')
				return '<span style="color:red">' + _('Execution failed') + '</span>';
			return _('-----')

		},



		postMixInProperties: function() {
			this.inherited(arguments);
			this.standbyOpacity = 1;
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
			this.renderOverviewPage();
		},

		renderOverviewPage: function(containers, superordinates) {
			// render grid page
			this._overviewPage = new Page({
				headerText: this.description,
				helpText: ''
			});

			this.addChild(this._overviewPage);

			// umc.widgets.ExpandingTitlePane is an extension of dijit.layout.BorderContainer
			var titlePane = new ExpandingTitlePane({
				title: _('Test results')
			});
			this._overviewPage.addChild(titlePane);



			// define grid actions
			var actions = [{
				name: 'run',
				label: _('Run'),
				description: _('Run selected tests'),
				iconClass: 'umcIconPlay',
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, '_runTests')
			}, {
				name: 'details',
				label: _('Details'),
				description: _('View details'),
				iconClass: 'umcIconView',
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, '_viewDetails')
			}, {
				name: 'submit',
				label: _('Submit'),
				description: _('Submit resulsts to Univention Support'),
				iconClass: 'umcIconReport',
				isStandardAction: true,
				isMultiAction: true,
				callback: lang.hitch(this, '_submitResults')
			}];

			// define the grid columns
			var columns = [{
				name: 'title',
				label: _('Title'),
				width: '35%'
			}, {
				name: 'timestamp',
				label: _('Last executed'),
				width: '20%',
				formatter: this.timestampFormatter
			}, {
				name: 'summary',
				label: _('Problem summary'),
				width: '35%',
				formatter: this.summaryFormatter
			}, {
				name: 'result',
				label: _('Last result'),
				width: '10%',
				formatter: this.resultFormatter
			}];

			// generate the data grid
			this._grid = new Grid({
				// property that defines the widget's position in a dijit.layout.BorderContainer,
				// 'center' is its default value, so no need to specify it here explicitely
				// region: 'center',
				actions: actions,
				defaultAction: 'details',
				// defines which data fields are displayed in the grids columns
				columns: columns,
				// a generic UMCP module store object is automatically provided
				// as this.moduleStore (see also store.getModuleStore())
				moduleStore: this.moduleStore,
				query: {searchPattern: ''}

			});

			// add the grid to the title pane
			titlePane.addChild(this._grid);


			//
			// search form
			//

			// add remaining elements of the search form
			var widgets = [{
				type: TextBox,
				name: 'searchPattern',
				description: _('Specifies the substring pattern which is searched for in the test names'),
				label: _('Search pattern')
			}];

			// the layout is an 2D array that defines the organization of the form elements...
			// here we arrange the form elements in one row and add the 'submit' button
			var layout = [
				[ 'searchPattern', 'submit' ]
			];

			// generate the search form
			this._searchForm = new SearchForm({
				// property that defines the widget's position in a dijit.layout.BorderContainer
				region: 'top',
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

			// add search form to the title pane
			titlePane.addChild(this._searchForm);

			//
			// conclusion
			//

			// we need to call page's startup method manually as all widgets have
			// been added to the page container object
			this._overviewPage.startup();

			// create a DetailPage instance
			this._detailPage = new DetailPage({
				moduleStore: this.moduleStore,
				timestampFormatter: this.timestampFormatter,
				summaryFormatter: this.summaryFormatter,
				resultFormatter: this.resultFormatter
			});
			this.addChild(this._detailPage);

			// connect to the onClose event of the detail page... we need to manage
			// visibility of sub pages here
			// ... widget.on() will destroy signal handlers upon widget
			// destruction automatically
			this._detailPage.on('close', lang.hitch(this, function() {
				this.selectChild(this._overviewPage);
			}));
		},

		_runTests: function(selectedPlugins) {
				this.standby(true);
				this.umcpCommand('supphealth/run', selectedPlugins).then(lang.hitch(this, function(ids, items) {
					this.standby(false);
					this._grid.filter({searchPattern: ''});
				}), lang.hitch(this, function(error) {
					this.standby(false);
				}));
		},

		_viewDetails: function(ids, items) {
			if (ids.length != 1) {
				// should not happen
				return;
			}

			this.selectChild(this._detailPage);
			this._detailPage.load(ids[0]);
		},

		_submitResults: function() {
			dialog.alert(_('Feature not implemented yet'));
		}
	});
});
