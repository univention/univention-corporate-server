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
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/DateBox",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/admindiary"
], function(declare, lang, array, dialog, tools, Page, Grid, SearchForm, DateBox, ComboBox, TextBox, SearchBox, _) {
	return declare("umc.modules.admindiary.OverviewPage", [ Page ], {

		moduleStore: null,
		_grid: null,
		_searchWidget: null,

		// values for comboboxes
		tags: null,
		authors: null,
		sources: null,
		events: null,

		helpText: _('This module lists all entries of the Admin Diary. You may comment on the events.'),
		fullWidth: true,

		buildRendering: function() {
			this.inherited(arguments);

			var columns = [{
				name: 'date',
				label: _('Date'),
			}, {
			//	name: 'event',
			//	label: _('Event'),
			//}, {
				name: 'hostname',
				label: _('Source'),
			}, {
			//	name: 'username',
			//	label: _('Author'),
			//}, {
				name: 'message',
				label: _('Message'),
				width: '50%',
			}, {
			//	name: 'tags',
			//	label: _('Tags'),
			//	formatter: lang.hitch(this, function(value) {
			//		if (value) {
			//			return '<ul><li>' + value.join('</li><li>') + '</li></ul>';
			//		} else {
			//			return '';
			//		}
			//	})
			//}, {
				name: 'amendments',
				label: _('Amendments'),
				width: '10%',
				formatter: lang.hitch(this, function(value) {
					if (value) {
						return _('☰');
					} else {
						return '';
					}
				})
			}];
			var actions = [{
					name: 'show',
					label: _('Show'),
					isMultiAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, function(ids) {
						var context_id = ids[0];
						this.onShowDetails(context_id);
					})
				}];

			this._grid = new Grid({
				region: 'main',
				defaultAction: 'show',
				columns: columns,
				actions: actions,
				moduleStore: this.moduleStore
			});

			var makeValues = function(values) {
				var arr = [{label: '', id: ''}];
				return arr.concat(array.map(values, function(value) {
					return {label: value, id: value};
				}));
			};
			var widgets = [{
				type: DateBox,
				label: _("From"),
				value: new Date(new Date().getTime() - 7 * 24 * 60 * 60 * 1000),
				sizeClass: 'TwoThirds',
				name: 'time_from'
			}, {
				type: DateBox,
				label: _("Until"),
				value: new Date(),
				sizeClass: 'TwoThirds',
				name: 'time_until'
			}, {
				type: ComboBox,
				label: _("Tags"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.tags),
				name: 'tag'
			}, {
				type: ComboBox,
				label: _("Event"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.events),
				name: 'event'
			}, {
				type: ComboBox,
				label: _("Author"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.authors),
				name: 'username'
			}, {
				type: ComboBox,
				label: _("Source"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.sources),
				name: 'hostname'
			}, {
				type: SearchBox,
				name: 'message',
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
				layout: [['time_from', 'tag', 'username'],
					['time_until', 'event', 'hostname'],
					['message']],
				onSearch: lang.hitch(this._grid, 'filter')
			});

			this.addChild(this._searchWidget);
			this.addChild(this._grid);

			this._searchWidget.onSubmit();
			this._grid.resize();
		},

		onShowDetails: function() {
		},
	});
});
