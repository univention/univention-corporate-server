/*
 * Copyright 2016-2017 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"umc/widgets/Grid",
	"umc/widgets/Module",
	"umc/widgets/NumberSpinner",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/TextBox",
	"umc/modules/logview/DetailPage",
	"umc/i18n!umc/modules/logview"
], function(declare, lang, on, Grid, Module, NumberSpinner, Page, SearchForm, TextBox, DetailPage, _) {
	return declare("umc.modules.logview", [Module], {

		standbyOpacity: 1,
		idProperty: 'filename',
		_grid: null,
		_searchPage: null,
		_detailPage: null,

		buildRendering: function() {
			this.inherited(arguments);

			this.standby(true);

			this._searchPage = new Page({
				headerText: this.description,
				helpText: _("This module lists the logfiles of the system. The files can be filtered by their filenames and contents. The results can be clicked to view the files' contents.")
			});
			this.addChild(this._searchPage);

			var actions = [{
				name: 'view',
				label: _('View'),
				description: _('View the selected file'),
				iconClass: 'umcIconView',  // or umcIconReport
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, '_view')
			}];

			var columns = [{
				name: 'filename',
				label: _('Filename'),
				width: '70%'
			}, {
				name: 'lines',
				label: _('Lines'),
				width: '15%'
			}, {
				name: 'filesize',
				label: _('Filesize'),
				width: '15%',
				formatter: this._formatBytes
			}];

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				defaultAction: 'view',
				query: {name: ''}
			});

			var widgets = [{
				type: TextBox,
				name: 'logfile',
				description: _('Specifies the substring pattern which is searched for in the filenames'),
				label: _('Filename')
			}, {
				type: TextBox,
				name: 'pattern',
				description: _("Specifies the substring pattern which is searched for in the files' contents"),
				label: _('Search for content')
			}, {
				type: NumberSpinner,
				name: 'radius',
				description: _('Specifies how many lines of context around an occurrence of the search pattern are displayed'),
				label: _('Search result context radius'),
				constraints: {min: 0, max: 99, places: 0},
				value: 5
			}];

			var layout = [
				['logfile', 'pattern', 'radius', 'submit']
			];

			this._searchForm = new SearchForm({
				region: 'nav',
				widgets: widgets,
				layout: layout,
				onSearch: lang.hitch(this, function(values) {
					this._grid.filter(values);
				})
			});

			on.once(this._searchForm, 'valuesInitialized', lang.hitch(this, function() {
				this.standby(false);
			}));

			this._searchPage.addChild(this._searchForm);
			this._searchPage.addChild(this._grid);
			this._searchPage.startup();

			this._detailPage = new DetailPage();
			this.addChild(this._detailPage);
			this._detailPage.on('close', lang.hitch(this, function() {
				this._searchForm.getWidget('pattern').set('value', this._detailPage.getPattern());
				this.selectChild(this._searchPage);
			}));
		},

		_view: function(ids, items) {
			var filename = ids[0];
			var values = this._searchForm.get('value');
			this._detailPage.load(filename, values.pattern, values.radius);
			this.selectChild(this._detailPage);
		},

		_formatBytes: function(value) {
			var units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];  // or ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
			var base = 1024;  // or 1000
			var precision = 10;  // 10^1 -> 1 decimal place
			var magnitude = 0;
			while (value >= base && magnitude < units.length - 1) {
				value /= base;
				magnitude++;
			}
			return Math.round(value * precision) / precision + ' ' + units[magnitude];
		}
	});
});
