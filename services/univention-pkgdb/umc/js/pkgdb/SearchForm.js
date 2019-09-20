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
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/pkgdb"
], function(declare, lang, array, tools, Form, TextBox, ComboBox, _) {

	// Search form as a separate class, so the gory details are hidden from the main page.
	//
	return declare("umc.modules.pkgdb.SearchForm", [Form], {

		// Some status variables
		_pattern_needed: true, // true if a pattern is required by this key
		_pattern_is_list: false, // true if pattern is ComboBox. false if TextBox.
		_submit_allowed: false, // true if current input allows SUBMIT (including that no queries are pending)

		// true while the corresponding query is pending
		_keys_pending: true,
		_proposals_pending: false,

		postMixInProperties: function() {
			lang.mixin(this, {
				widgets:  [{
					type: ComboBox,
					name: 'key',
					label: _("Search for:"),
					size: 'TwoThirds',
					sortDynamicValues: false,
					dynamicValues: 'pkgdb/keys',
					dynamicOptions: {page: this.pageKey},
					onDynamicValuesLoaded: lang.hitch(this, function() {
						this._set_selection_to_first_element('key');
						this._set_query_pending('key', false);
					})
				}, {
					type: ComboBox,
					name: 'pattern_list',
					depends: 'key',
					label: _("Pattern"),
					sortDynamicValues: false,
					dynamicValues: lang.hitch(this, function() {
						return this._proposals_query();
					}),
					onDynamicValuesLoaded: lang.hitch(this, function(values) {
						this._handle_proposals(values);
						this._set_query_pending('proposal', false);
					})
				}, {
					type: TextBox,
					name: 'pattern_text',
					label: _("Pattern"),
					// inherits from dijit.form.ValidationTextBox, so we can use its
					// validation abilities
					regExp: '^[A-Za-z0-9_.*?-]+$'  // [: alnum: ] and these:  _ - . * ?
				}],
				layout:  [['key', 'pattern_text', 'pattern_list', 'submit']],
				buttons:  [{
					name: 'submit',
					label: _("Search")
				}]
			});

			// call the postMixinProperties of inherited classes AFTER! we have
			// added our constructor args!
			this.inherited(arguments);

		},

		buildRendering: function() {
			this.inherited(arguments);

			this.showWidget('pattern_text', false);
			this.showWidget('pattern_list', false);

			// whenever one of our 'pending' vars is changed...
			array.forEach(['_keys_pending', '_proposals_pending', 'key', 'pattern_text', 'pattern_list'], function(key) {
				this.own(this.watch(key, lang.hitch(this, function() {
					this._handle_query_changes();
				})));
			}, this);
		},

		// ---------------------------------------------------------------------
		//
		//		functions to be called from outside
		//
		//		These are the functions that are called by the instance
		//		that created us (our ancestor).
		//
		// ---------------------------------------------------------------------

		// Reads the corresponding dialog elements and returns the current query
		// as a dict with key, operand and pattern.
		//
		// If this is called even while the dialog state doesn't allow executing
		// a query -> return an empty dict.
		getQuery: function() {
			var query = {};

			var crit = this.getWidget('key').get('value');
			if (crit !== '_') {
				query.key = crit;
				if (this._submit_allowed) {
					if (this._pattern_is_list) {
						query.pattern = this.getWidget('pattern_list').get('value');
					} else {
						query.pattern = this.getWidget('pattern_text').get('value');
					}
				}
			}

			return query;
		},

		// -------------------------------------------------------------------
		//
		//		dynamic queries
		//
		//		It is not enough to have 'dynamicValues' and 'dynamicOptions'
		//		at widget construction time; we need variable options while
		//		the widget is alive.
		//
		//		These functions can't return the Deferred as returned
		//		from umcpCommand since that would hand over the whole response
		//		(with 'status', 'message' and 'result' elements) to the ComboBox.
		//		Instead, we return a chained Deferred that extracts the
		//		'result' element from there.
		//
		// -------------------------------------------------------------------

		// returns proposals for the 'pattern' field for a given
		// key. (pageKey is added silently)
		_proposals_query: function() {
			this._set_query_pending('proposal', true);
			try {
				var key = this.getWidget('key').get('value');

				return tools.umcpCommand('pkgdb/proposals', {
					page: this.pageKey,
					key: key
				}).then(function(data) { return data.result; });
			} catch(error) {
				console.error("proposals_query:  " + error.message);
			}
			return null;
		},

		// ------------------------------------------------------------
		//
		//		handlers for return values
		//
		// ------------------------------------------------------------

		// handles the result (and especially:  the result type) of the
		// proposals returned by the 'pkgdb/proposals' query
		_handle_proposals: function(values) {
			var is_single = typeof values === "string";
			this._pattern_is_list = !is_single;  // remember for later.
			if (is_single) {
				this.getWidget('pattern_text').set('value', values);
			} else {
				this._set_selection_to_first_element('pattern_list');
			}
			// values are set. now show/hide appropriately, but only if needed.
			if (this._pattern_needed) {
				this.showWidget('pattern_text', is_single);
				this.showWidget('pattern_list', !is_single);
			}
		},

		// sets state of 'this query is pending' in a boolean variable
		// and in the 'disabled' state of the corresponding dialog element(s)
		_set_query_pending: function(element, on) {
			var bv = '_' + element + 's_pending';
			this.set(bv, on);

		},

		_set_selection_to_first_element: function(name) {
			var widget = this.getWidget(name);
			if (widget) {
				widget.set('value', widget._firstValueInList);
			}
		},

		// We can't inhibit that onSubmit() is being called even if we have
		// explicitly set a widget to invalid... why do widgets have this
		// feature if the form doesn't honor it?
		onSubmit: function() {
			// the 'onChange' handler of the textbox is not invoked until the focus
			// has left the field... so we have to do a last check here in case
			// the text changed.
			this._handle_query_changes();

			if (this._submit_allowed) {
				this.onExecuteQuery(this.getQuery());
			}
			return this.inherited(arguments);
		},

		// an internal callback for everything that changes a query or pattern.
		// should call the external callback 'onQueryChanged' only if something has
		// changed. This maintains all internal variables that reflect the state of
		// the current entry and the executability of the query.
		_handle_query_changes: function() {
			// start with:  allowed if none of our dynamicValues queries is pending
			var allow = !(this._keys_pending || this._proposals_pending);

			// only allow if the 'key' position is not '--- select one ---'
			allow = allow && (this.getWidget('key').get('value') !== '_');

			// check validation for all elements that must be valid
			if (allow) {
				array.forEach(this._widgets, function(w) {
					var widget = this._widgets[w];
					var n = widget.name;
					var toprocess = true;
					if (n.substr(0, 8) === 'pattern_') {
						if (this._pattern_needed) {
							if (((this._pattern_is_list) && (n === 'pattern_text')) || ((!this._pattern_is_list) && (n === 'pattern_list'))) {
								toprocess = false;
							}
						} else {
							// no pattern required:  pattern_text AND pattern_list should
							// should be ignored
							toprocess = false;
						}
					}
					if (toprocess) {
						if (!widget.isValid()) {
							allow = false;
						}
					}
				}, this);
			}

			if (allow !== this._submit_allowed) {
				this._submit_allowed = allow;
			}
		},

		// our follow-up of the submit event, called only if submit is allowed.
		// For the convenience of the caller, we pass the current query.
		onExecuteQuery: function(/*query*/) {
		},

		// the invoking Page or Module can listen here to know that the query is become
		// ready or disabled. Internal function _handle_query_changes() maintains all
		// state variables and calls this only if the state has changed.
		onQueryChanged: function(/*query*/) {
		}

	});
});
