/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/_base/array",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/admindiary"
], function(declare, lang, array, dialog, tools, Module, Page, Grid, SearchForm, SearchBox, _) {
	return declare("umc.modules.admindiary", [ Module ], {

		moduleStore: null,
		_grid: null,
		_page: null,
		_searchWidget: null,

		idProperty: 'admindiary',

		buildRendering: function() {
			this.inherited(arguments);

			this._page = new Page({
				helpText: _('This module lists all entries of the Admin Diary. You may comment on the events.'),
				fullWidth: true
			});
			this.addChild(this._page);

			var columns = [{
				name: 'date',
				label: _('Date')//,
			}, {
				name: 'message',
				label: _('Message'),
			}, {
				name: 'amendments',
				label: _('Amendments'),
				width: '15%',
				formatter: lang.hitch(this, function(value) {
					if (value) {
						return _('☰');
					} else {
						return '';
					}
				})
			}];

			this._grid = new Grid({
				region: 'main',
				columns: columns,
				moduleStore: this.moduleStore,
				query: {
					pattern: ''
				}
			});

			var widgets = [{
				type: SearchBox,
				name: 'pattern',
				value: '',
				inlineLabel: _('Search...'),
				onSearch: lang.hitch(this, function() {
					this._searchWidget.submit();
				})
			}];

			this._searchWidget = new SearchForm({
				region: 'nav',
				hideSubmitButton: true,
				widgets: widgets,
				layout: ['pattern'],
				onSearch: lang.hitch(this._grid, 'filter')
			});

			this._page.addChild(this._searchWidget);
			this._page.addChild(this._grid);

			this._page.startup();
		}
	});
});
