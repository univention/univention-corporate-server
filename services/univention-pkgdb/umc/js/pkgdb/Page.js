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
	"dojo/Deferred",
	"dojo/topic",
	"dojo/dom-class",
	"umc/tools",
	"umc/store",
	"umc/widgets/Grid",
	"umc/widgets/Page",
	"umc/modules/pkgdb/SearchForm",
	"umc/modules/pkgdb/KeyTranslator",
	"umc/i18n!umc/modules/pkgdb"
], function(declare, lang, Deferred, topic, domClass, tools, store, Grid, Page, SearchForm, KeyTranslator, _) {

	// Page with a unified layout
	//
	//	-	one-line search form (for now...?)
	//	-	results grid
	//
	// Which page ('flavor') to show is determined by the 'pageKey'
	// attribute being set by the constructor call.
	//
	return declare("umc.modules.pkgdb.Page", [Page, KeyTranslator], {

		_grid: null,  // holds the results grid if query was invoked at least once
		_last_table_structure: null,  // remember last table structure
		_current_query: null,  // what is being executed right now

		buildRendering: function() {
			this.inherited(arguments);

			this._searchform = new SearchForm({
				region: 'main',
				pageKey: this.pageKey
			});
			this.addChild(this._searchform);

			// Listen to the submit event
			this._searchform.on('ExecuteQuery', lang.hitch(this, function(query) {
				this._execute_query(query);
			}));
		},

		postCreate: function() {
			this.inherited(arguments);
			this.standbyDuring(this._searchform.ready()).then(lang.hitch(this, function() {
				this._build_columns(this._searchform.getQuery());
			}));
		},

		_execute_query: function(query) {
			this._build_columns(query).then(lang.hitch(this, function() {
				// Execute the given query (a.k.a. filter) on the grid
				this._grid.filter(lang.mixin({page: this.pageKey }, this._current_query));
			}));

			topic.publish('/umc/actions', 'pkgdb', this.pageKey, query.key, 'search');
		},

		// fetches the structure of the result grid.
		_build_columns: function(query) {
			this._current_query = query;

			return tools.umcpCommand('pkgdb/columns', {
				page: this.pageKey,
				key: this._current_query.key
			}).then(lang.hitch(this, function(data) {
				return this._create_table(data.result);
			}));
		},

		// Creates the given result table. 'fields' is an array of column names.
		// The corresponding query is already stored in this._current_query.
		_create_table: function(fields) {
			var deferred = new Deferred();
			// determine if we have already a grid structured like that
			var grid_usable = false;
			var sig = fields.join(':');
			if (this._grid) {
				if (this._last_table_structure && (this._last_table_structure === sig)) {
					grid_usable = true;
				}
			}
			this._last_table_structure = sig;

			if (!grid_usable) {
				var columns = [];
				tools.forIn(fields, lang.hitch(this, function(f) {
					var fname = fields[f];
					var entry = {
						name: fname,
						label: fname
					};
					var props = this._field_options(fname);
					if (props) {
						lang.mixin(entry, props);
					}
					columns.push(entry);
				}));

				var newgrid = new Grid({
					region: 'main',
					actions: [],
					columns: columns,
					moduleStore: store(fields[0], 'pkgdb'),
					gridOptions: {selectionMode: 'none'}
				});

				if (this._grid) {
					// detach and free old grid instance
					this.removeChild(this._grid);
					this._grid.uninitialize();
					this._grid = null;
				}
				this._grid = newgrid;
				this.addChild(this._grid);
			}

			domClass.toggle(this._grid.domNode, 'dijitDisplayNone', false);

			deferred.resolve(true);
			return deferred;
		}
	});
});
