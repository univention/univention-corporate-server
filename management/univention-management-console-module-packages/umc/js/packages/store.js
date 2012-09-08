/*
 * Copyright 2011-2012 Univention GmbH
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
	"dojo/Deferred",
	"dojo/store/util/QueryResults",
	"dojo/store/Observable",
	"umc/tools"
], function(declare, lang, array, Deferred, QueryResults, Observable, tools) {
	var _UmcpModuleStore = declare("umc.modules.packages.store.UmcpModuleStore", null, {
		idProperty: '',

		storePath: '',

		umcpCommand: tools.umcpCommand,

		constructor: function(params) {
			lang.mixin(this, params);
		},

		getIdentity: function(object) {
			return object[this.idProperty];
		},

		_genericCmd: function(type, param) {
			if (this._doingTransaction) {
				this._addTransactions(type, [param]);
			}
			else {
				return this._genericMultiCmd(type, [param]).
					then(function(results) {
						/*
						 * BEGIN CHANGED
						 * return 400 if results is an object
						 * as returned from backend-sanitizers
						 */
						if (results instanceof Array) {
							return results[0];
						} else {
							return {
								'status': 400,
								'result': results['0']['object']
							}		
						}
						/*
						 * END CHANGED
						 */
					});
			}
		},

		_genericMultiCmd: function(type, params) {
			if (this._doingTransaction) {
				this._addTransactions(type, params);
			}
			else {
				/*
				 * BEGIN CHANGED
				 * dont handle errors automatically
				 * otherwise only status 200 is propagated
				 * TODO: handle non-validation-error-status
				 * the way it was handled.
				 */
				return this.umcpCommand(this.storePath + '/' + type, params, false).
					/*
					 * END CHANGED
					 */
					then(lang.hitch(this, function(data) {
						var res = lang.getObject('result', false, data);

						if (!this._noEvents && ('remove' == type || 'put' == type || 'add' == type)) {
							this.onChange();
						}

						return res;
					}));
			}
		},

		get: function(id) {
			return this._genericCmd('get', id);
		},

		put: function(object, options) {
			return this._genericCmd('put', {
				object: object,
				options: options || null
			});
		},

		add: function(object, options) {
			return this._genericCmd('add', {
				object: object,
				options: options || null
			});
		},

		remove: function( object, options ) {
			return this._genericCmd('remove', {
				object: object,
				options: options || null
			} );
		},

		query: function(_query, options) {
			var query = {};
			var nQueryEl = 0;
			tools.forIn(_query, function(ikey, ival) {
				query[ikey] = (typeof ival == "string" || typeof ival == 'boolean' || 'null' === ival) ? ival : String(ival);
				++nQueryEl;
			}, this, true);
			var deferred = new Deferred();
			if (nQueryEl) {
				deferred = this.umcpCommand(this.storePath + '/query', query);
				deferred = deferred.then(function(data) {
					var result = data.result;
					var sort = lang.getObject('sort', false, options);
					if (sort) {
						result.sort(tools.cmpObjects(sort));
					}
					return result;
				});
			}
			else {
				deferred.callback([]);
			}
			return QueryResults(deferred);
		},

		_doingTransaction: false,

		_groupedTransactions: [],

		_addTransactions: function(type, params) {
			var lastGroupType = (0 === this._groupedTransactions.length ?
				'' : this._groupedTransactions[this._groupedTransactions.length - 1].type);
			if (lastGroupType != type) {
				var newGroup = {
					type: type,
					params: params
				};
				this._groupedTransactions.push(newGroup);
			}
			else {
				var lastGroup = this._groupedTransactions[this._groupedTransactions.length - 1];
				lastGroup.params = lastGroup.params.concat(params);
			}
		},

		_commitTransactions: function() {
			var deferred = new Deferred();
			deferred.resolve();
			var results = [];
			this._doingTransaction = false;
			this._noEvents = true;
			var dataModified = false;
			array.forEach(this._groupedTransactions, lang.hitch(this, function(igroup) {
				dataModified = dataModified || 'remove' == igroup.type || 'put' == igroup.type || 'add' == igroup.type;

				deferred = deferred.then(lang.hitch(this, function() {
					return this._genericMultiCmd(igroup.type, igroup.params).then(function(data) {
						results = results.concat(data);
						return null;
					});
				}));
			}));

			var _cleanup = lang.hitch(this, function() {
				this._noEvents = false;
				if (dataModified) {
					this.onChange();
				}

				this._groupedTransactions = [];

			});

			deferred = deferred.then(lang.hitch(this, function() {
				_cleanup();

				return results;
			}), _cleanup);

			return deferred;
		},

		_abortTransactions: function() {
			this._groupedTransactions = [];
			this._doingTransaction = false;
		},

		transaction: function() {
			tools.assert(!this._doingTransaction, 'Another UMCP transaction is already being processed, cannot perform two transactions simultaneously.');
			this._doingTransaction = true;
			return {
				commit: lang.hitch(this, this._commitTransactions),
				abort: lang.hitch(this, this._abortTransactions)
			};
		},

		_noEvents: false,
		onChange: function() {
		}
	});

	var _moduleStores = {};

	return function(/*String*/ idProperty, /*String*/ storePath, /*String?*/ moduleFlavor) {

		var key = storePath + '@' + (moduleFlavor || 'default');
		if (!_moduleStores[key]) {
			_moduleStores[key] = Observable(new _UmcpModuleStore({
				idProperty: idProperty,
				storePath: storePath,
				umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
					return tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || moduleFlavor );
				}
			}));
		}
		return _moduleStores[key];
	};
});

