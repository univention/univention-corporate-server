/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/date/locale",
	"dojox/html/entities",
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
], function(declare, lang, array, locale, entities, dialog, tools, Page, Grid, SearchForm, DateBox, ComboBox, TextBox, SearchBox, _) {
	return declare("umc.modules.admindiary.OverviewPage", [ Page ], {

		'class': 'admindiaryOverview',
		moduleStore: null,
		_grid: null,
		_searchForm: null,

		// values for comboboxes
		tags: null,
		authors: null,
		sources: null,
		events: null,

		helpText: _('This module lists all entries of the Admin Diary. You may comment on the events.'),
		fullWidth: true,

		ALL_ID: '__all__',

		postMixInProperties: function() {
			this.inherited(arguments);
			this.footerButtons = [{
				name: 'previous',
				align: 'left',
				label: _("Previous week"),
				callback: lang.hitch(this, 'previousWeek')
			}, {
				name: 'next',
				align: 'right',
				label: _("Next week"),
				callback: lang.hitch(this, 'nextWeek')
			}];
		},

		iconFormatter: function(value, item) {
			return lang.replace('<img src="modules/admindiary/icons/{icon}.svg" height="{height}" width="{width}" style="float:left; margin-right: 5px" /> {value}', {
				icon: item.icon,
				height: '32px',
				width: '32px',
				value: entities.encode(value)
			});
		},

		dateFormatter: function(value) {
			return locale.format(new Date(value));
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._autoSearch = false;
			this._advancedSearch = false;

			var columns = [{
				name: 'message',
				label: _('Message'),
				width: '75%',
				formatter: lang.hitch(this, 'iconFormatter')
			}, {
				name: 'date',
				label: _('Date'),
				width: '15%',
				formatter: lang.hitch(this, 'dateFormatter')
			}, {
				name: 'comments',
				label: _('Comments'),
				width: '10%',
				formatter: function(value) { return value ? '📝' : ''; }
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
				//defaultAction: 'show',
				columns: columns,
				sortIndex: 2,
				//actions: actions,
				gridOptions: {
					selectionMode: 'none'
				},
				moduleStore: this.moduleStore
			});

			var makeValues = function(values, all_id) {
				var arr = [{label: _('All'), id: all_id}];
				return arr.concat(array.map(values, function(value) {
					return {label: value, id: value};
				}));
			};
			var widgets = [{
				type: DateBox,
				label: _("From"),
				value: new Date(new Date().getTime() - 6 * 24 * 60 * 60 * 1000),
				sizeClass: 'OneThird',
				onChange: lang.hitch(this, 'autoSearch'),
				name: 'time_from'
			}, {
				type: DateBox,
				label: _("Until"),
				value: new Date(),
				sizeClass: 'OneThird',
				onChange: lang.hitch(this, 'autoSearch'),
				name: 'time_until'
			}, {
				type: ComboBox,
				label: _("Tags"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.tags, this.ALL_ID),
				value: this.ALL_ID,
				onChange: lang.hitch(this, 'autoSearch'),
				visible: false,
				name: 'tag'
			}, {
				type: ComboBox,
				label: _("Event"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.events, this.ALL_ID),
				value: this.ALL_ID,
				onChange: lang.hitch(this, 'autoSearch'),
				visible: false,
				name: 'event'
			}, {
				type: ComboBox,
				label: _("Author"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.authors, this.ALL_ID),
				value: this.ALL_ID,
				onChange: lang.hitch(this, 'autoSearch'),
				visible: false,
				name: 'username'
			}, {
				type: ComboBox,
				label: _("Source"),
				sizeClass: 'TwoThirds',
				staticValues: makeValues(this.sources, this.ALL_ID),
				value: this.ALL_ID,
				onChange: lang.hitch(this, 'autoSearch'),
				visible: false,
				name: 'hostname'
			}, {
				type: SearchBox,
				name: 'message',
				value: '',
				sizeClass: 'TwoThirds',
				inlineLabel: _('Search...'),
				onSearch: lang.hitch(this, function() {
					this._searchForm.submit();
				})
			}];

			var buttons = [{
				name: 'toggleSearch',
				showLabel: false,
				labelConf: {
					'class': 'umcSearchFormSubmitButton'
				},
				iconClass: 'umcDoubleRightIcon',
				label: _('Advanced Search'),
				callback: lang.hitch(this, 'toggleSearch')
			}];
			this._searchForm = new SearchForm({
				region: 'nav',
				hideSubmitButton: true,
				widgets: widgets,
				buttons: buttons,
				layout: [['time_from', 'time_until', 'message', 'toggleSearch'],
					['tag', 'event', 'hostname', 'username']]
			});
			this._searchForm.on('Search', lang.hitch(this, function(options) {
				array.forEach(['tag', 'event', 'hostname', 'username'], lang.hitch(this, function(widgetName) {
					if (options[widgetName] == this.ALL_ID) {
						delete options[widgetName];
					}
				}));
				this._grid.filter(options).then(lang.hitch(this, function() {
					this._autoSearch = true;
				}));
			}));

			this.addChild(this._searchForm);
			this.addChild(this._grid);

			this._searchForm.onSubmit();
			this._grid.resize();

			this._grid._grid.set('selectionMode', 'single');
			this._grid._grid.on('dgrid-select', lang.hitch(this, 'clickRow'));
		},

		nextWeek: function() {
			var values = this._searchForm.get('value');
			if (! values.time_from) {
				return;
			}
			var time_from = new Date(new Date(values.time_from).getTime() + 7 * 24 * 60 * 60 * 1000);
			var time_until = new Date(time_from.getTime() + 6 * 24 * 60 * 60 * 1000);
			this._autoSearch = false;
			this._searchForm.getWidget('time_from').set('value', time_from);
			this._searchForm.getWidget('time_until').set('value', time_until);
			this._searchForm.onSubmit();
		},

		previousWeek: function() {
			var values = this._searchForm.get('value');
			if (! values.time_until) {
				return;
			}
			var time_until = new Date(new Date(values.time_until).getTime() - 7 * 24 * 60 * 60 * 1000);
			var time_from = new Date(time_until.getTime() - 6 * 24 * 60 * 60 * 1000);
			this._autoSearch = false;
			this._searchForm.getWidget('time_from').set('value', time_from);
			this._searchForm.getWidget('time_until').set('value', time_until);
			this._searchForm.onSubmit();
		},

		toggleSearch: function() {
			this._advancedSearch = !this._advancedSearch;
			array.forEach(['username', 'tag', 'event', 'hostname'], lang.hitch(this, function(widgetName) {
				this._searchForm.getWidget(widgetName).set('visible', this._advancedSearch);
			}));
			var button = this._searchForm.getButton('toggleSearch');
			if (this._advancedSearch) {
				button.set('label', _('Simple Search'));
				button.set('iconClass', 'umcDoubleLeftIcon');
			} else {
				button.set('label', _('Advanced Search'));
				button.set('iconClass', 'umcDoubleRightIcon');
			}
		},

		autoSearch: function() {
			if (this._autoSearch) {
				this._searchForm.onSubmit();
			}
		},

		clickRow: function(evt) {
			var item = evt.rows[0];
			this._grid._grid.deselect(item);
			this.onShowDetails(item.id);
		},

		onShowDetails: function() {
		},
	});
});
