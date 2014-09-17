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
/*global define*/

define([
	'dojo/_base/declare',
	'dojo/_base/lang',
	'dojo/_base/array',
	'dojo/promise/all',
	'dojo/on',
	'umc/dialog',
	'umc/tools',
	'umc/widgets/Grid',
	'umc/widgets/Page',
	'umc/widgets/SearchForm',
	'umc/widgets/Module',
	'umc/widgets/TextBox',
	'umc/widgets/ComboBox',
	'umc/modules/diagnostic/DetailPage',
	'umc/i18n!umc/modules/diagnostic'
], function(declare, lang, array, all, on, dialog, tools, Grid, Page, SearchForm, Module, TextBox, ComboBox, DetailPage, _) {
	return declare('umc.modules.diagnostic',  Module, {

		_grid: null,
		_overviewPage: null,
		_detailPage: null,
		idProperty: 'plugin',

		timestampFormatter: function(value) {
			if (!value) {
				return _('Never');
			}
			return value;
		},

		summaryFormatter: function(value) {
			if (!value) {
				return _('-----');
			}
			return value;
		},

		resultFormatter: function(value) {
			if (value == '0') {
				return '<span style="color:green">' + _('Successful') + '</span>';
			}
			else if (value == '1') {
				return '<span style="color:orange">' + _('Problems detected') + '</span>';
			}
			else if (value == '-1') {
				return '<span style="color:red">' + _('Execution failed') + '</span>';
			}
			return _('-----');
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.standbyOpacity = 1;
			this.fixModuleStore();
		},

		fixModuleStore: function() {
			this.moduleStore.get = lang.hitch(this.moduleStore, function(id, handleErrors) {
				var data = {};
				data[this.idProperty] = id;
				return this._genericCmd('get', data, handleErrors);
			});
			this.moduleStore.put = lang.hitch(this.moduleStore, function(object, options, handleErrors) {
				return this._genericCmd('put', object, handleErrors);
			});
			this.moduleStore.remove = lang.hitch(this.moduleStore, function(object, options, handleErrors) {
				return this._genericCmd('delete', object, handleErrors);
			});
			this.moduleStore._genericMultiCmd = lang.hitch(this.moduleStore, function(type, params, handleErrors) {
				var args = arguments;
				var that = this;
				return all(array.map(params, function(param) {
					return that.inherited('_genericMultiCmd', args, [type, param, handleErrors]);
				}));
			});
			this.moduleStore._genericCmd = lang.hitch(this.moduleStore, function(type, param, handleErrors) {
				if (this._doingTransaction) {
					this._addTransactions(type, [param]);
				}
				else {
					return this._genericMultiCmd(type, [param], handleErrors).then(function(results) {
						if (results && results instanceof Array) {
							return results[0];
						}
					});
				}
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.standby(true);

			this._overviewPage = new Page({
				headerText: this.description,
				helpText: ''
			});

			this.addChild(this._overviewPage);

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

			this._grid = new Grid({
				actions: actions,
				defaultAction: 'details',
				columns: columns,
				moduleStore: this.moduleStore,
				query: {pattern: ''}
			});

			this._overviewPage.addChild(this._grid);

			this._searchForm = new SearchForm({
				region: 'top',
				widgets: [{
					type: TextBox,
					name: 'pattern',
					description: _('Specifies the substring pattern which is searched for in the test names'),
					label: _('Search pattern')
				}],
				layout: [['pattern', 'submit']],
				onSearch: lang.hitch(this, function(values) {
					this._grid.filter(values);
				})
			});

			on.once(this._searchForm, 'valuesInitialized', lang.hitch(this, function() {
				// turn off the standby animation as soon as all form values have been loaded
				this.standby(false);
			}));

			this._overviewPage.addChild(this._searchForm);
			this._overviewPage.startup();

			this._detailPage = new DetailPage({
				moduleStore: this.moduleStore,
				timestampFormatter: this.timestampFormatter,
				summaryFormatter: this.summaryFormatter,
				resultFormatter: this.resultFormatter
			});
			this.addChild(this._detailPage);

			this._detailPage.on('close', lang.hitch(this, function() {
				this.selectChild(this._overviewPage);
			}));
		},

		_runTests: function(selectedPlugins) {
			this.standbyDuring(all(array.map(selectedPlugins, lang.hitch(this, function(plugin) {
				return this.umcpCommand('diagnostic/run', {plugin: plugin});
			})))).then(lang.hitch(this, function() {
				this._grid.filter({pattern: ''});
			}));
		},

		_viewDetails: function(ids, items) {
			this.selectChild(this._detailPage);
			this._detailPage.load(ids[0]);
		},

		_submitResults: function() {
			dialog.alert(_('Feature not implemented yet'));
		}
	});
});
