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
	"dojo/Deferred",
	"dojo/Evented",
	"dojo/store/util/QueryResults",
	"umc/tools"
], function(declare, lang, array, Deferred, Evented, QueryResults, tools) {
	var _UmcpModuleStore = declare("umc.store.UmcpModuleStore", [ Evented ], {
		// idProperty: String
		//		Indicates the property to use as the identity property.
		//		The values of this property should be unique.
		idProperty: '',

		// storePath: String
		//		UMCP URL of the module where query, set, remove, put, and add
		//		methods can be found.
		storePath: '',

		// umcpCommand: Function
		//		Reference to a particularly flavored umcpCommand.
		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		//TODO: for the future, it would be nice to work with query engines
		queryEngine: null,

		constructor: function(params) {
			lang.mixin(this, params);
			this._groupedTransactions = [];
		},

		getIdentity: function(object) {
			// summary:
			//		Returns an object's identity
			// object: Object
			//		The object to get the identity from
			//	returns: String

			//console.log('getIdentity: ' + json.stringify(arguments));
			return object[this.idProperty];
		},

		_genericCmd: function(type, param, handleErrors) {
			//console.log('_genericCmd: ' + json.stringify(arguments));
			if (this._doingTransaction) {
				this._addTransactions(type, [param]);
			}
			else {
				var singleHandleErrors;
				if (handleErrors) {
					singleHandleErrors = {};
					singleHandleErrors.onValidationError = function(message, data) {
						data = data[0].object;
						return handleErrors.onValidationError(message, data);
					};
				}
				return this._genericMultiCmd(type, [param], singleHandleErrors).
					then(function(results) {
						if (results && results instanceof Array) {
							return results[0];
						}
					});
			}
		},

		_genericMultiCmd: function(type, params, handleErrors) {
			//console.log('_genericMultiCmd: ' + json.stringify(arguments));
			if (this._doingTransaction) {
				this._addTransactions(type, params);
			}
			else {
				// send the UMCP command
				return this.umcpCommand(this.storePath + '/' + type, params, handleErrors).
					then(lang.hitch(this, function(data) {
						// make sure that we get an non-empty array
						//console.log('# _genericMultiCmd - deferred: data=' + String(data));
						var res = lang.getObject('result', false, data);

						// send event when changes occurred
						if (!this._noEvents && ('remove' == type || 'put' == type || 'add' == type)) {
							this.onChange();
						}

						//tools.assert(res && res instanceof Array && res.length == params.length,
						//	lang.replace('UMCP result from {0}/{1} did not yield an non-empty array!', [this.storePath, type]));
						return res;
					}));
			}
		},

		get: function(id, handleErrors) {
			//console.log('get: ' + json.stringify(arguments));
			//	summary:
			//		Retrieves an object by its identity. This will trigger an UMCP request
			//		calling the module method 'GET'.
			//	id: Number
			//		The identity to use to lookup the object
			//	returns: dojo/Deferred
			//		The object in the store that matches the given id.
			return this._genericCmd('get', id, handleErrors);
		},

		put: function(object, options, handleErrors) {
			//console.log('put: ' + json.stringify(arguments));
			// summary:
			//		Stores an object. This will trigger an UMCP request calling the module
			//		method 'SET'.
			// object: Object
			//		The object to store.
			// options:
			//		This parameter is currently ignored.
			// returns: Deferred
			return this._genericCmd('put', {
				object: object,
				options: options || null
			}, handleErrors);
		},

		add: function(object, options, handleErrors) {
			//console.log('add: ' + json.stringify(arguments));
			// summary:
			//		Stores an object. This will trigger an UMCP request calling the module
			//		method 'SET'.
			// object: Object
			//		The object to store.
			// options:
			//		This parameter is currently ignored.
			return this._genericCmd('add', {
				object: object,
				options: options || null
			}, handleErrors);
		},

		remove: function( object, options, handleErrors ) {
			//console.log('remove: ' + json.stringify(arguments));
			// summary:
			//		Deletes an object by its identity. This will trigger an UCMP request
			//		calling the module method 'UNSET'
			// object: Object
			//		The object to store.
			// options:
			//		bla fasel
			return this._genericCmd('remove', {
				object: object,
				options: options || null
			}, handleErrors );
		},

		query: function(_query, options) {
			//console.log('query: ' + json.stringify(arguments));
			// summary:
			//		Queries the store for objects. This will trigger a GET request to the server, with the
			//		query added as a query string.
			// query: Object
			//		The query to use for retrieving objects from the store.
			// options:
			//		Query options, such as 'sort' (see also tools.cmpObjects()).
			// returns: dojo/store/api/QueryResults
			//		The results of the query, extended with iterative methods.

			// if called via dojo/data/ObjectStore, queries can be translated to regexps
			var query = {};
			var nQueryEl = 0;
			tools.forIn(_query, function(ikey, ival) {
				query[ikey] = (typeof ival == "string" || ival instanceof Array || typeof ival == 'boolean' || null === ival) ? ival : String(ival);
				++nQueryEl;
			}, this, true);
			var deferred = new Deferred();
			if (nQueryEl) {
				// non-empty query
				deferred = this.umcpCommand(this.storePath + '/query', query);
				deferred = deferred.then(function(data) {
					var result = data.result;
					// if requested, sort the list
					var sort = lang.getObject('sort', false, options);
					if (sort) {
						result.sort(tools.cmpObjects(sort));
					}
					return result;
				});
			}
			else {
				// empty query -> return an empty list
				// this is the query the grid will send automatically at the beginning
				deferred.resolve([]);
			}
			return new QueryResults(deferred);
		},

		// _doingTransaction: Boolean
		//		Internal variable that tells user whether we are performing an transaction.
		_doingTransaction: false,

		_groupedTransactions: null,

		_addTransactions: function(type, params) {
			var lastGroupType = (0 === this._groupedTransactions.length ?
				'' : this._groupedTransactions[this._groupedTransactions.length - 1].type);
			if (lastGroupType != type) {
				// if no transactions have been submitted before or if the last type of
				// transaction does not match the current one, start a new group of transactions
				var newGroup = {
					type: type,
					params: params
				};
				this._groupedTransactions.push(newGroup);
			}
			else {
				// otherwise append the current commands to the last group
				var lastGroup = this._groupedTransactions[this._groupedTransactions.length - 1];
				lastGroup.params = lastGroup.params.concat(params);
			}
		},

		_commitTransactions: function() {
			// perform the transactions group-wise, the order of the command groups is respected,
			// a group of commands is submitted after the preceding one succeeded.
			var deferred = new Deferred();
			deferred.resolve();
			var results = [];
			this._doingTransaction = false;
			this._noEvents = true; // switch off event notifications
			var dataModified = false;
			array.forEach(this._groupedTransactions, lang.hitch(this, function(igroup) {
				// check whether the data is modified
				dataModified = dataModified || 'remove' == igroup.type || 'put' == igroup.type || 'add' == igroup.type;

				// chain all deferred commands
				deferred = deferred.then(lang.hitch(this, function() {
					return this._genericMultiCmd(igroup.type, igroup.params).then(function(data) {
						results = results.concat(data);
						//console.log(lang.replace('# deferred: i={0} data={1}', [i, String(data)]));
						return null;
					});
				}));
			}));

			var _cleanup = lang.hitch(this, function() {
				// switch back on events and send onChange event
				this._noEvents = false;
				if (dataModified) {
					this.onChange();
				}

				// remove all transactions
				this._groupedTransactions = [];

			});

			deferred = deferred.then(lang.hitch(this, function() {
				// clean up
				_cleanup();

				// return all results
				return results;
			}), _cleanup);

			return deferred;
		},

		_abortTransactions: function() {
			this._groupedTransactions = [];
			this._doingTransaction = false;
		},

		transaction: function() {
			// summary:
			//		Starts a new transaction.
			// description:
			//		Note that all transactions are (for now) executed in an undefined order.
			// returns: dojo.store.api.Store.Transaction
			//		This represents the new current transaction. `commit()` returns a
			//		`dojo/Deferred` object for all transactions.
			tools.assert(!this._doingTransaction, 'Another UMCP transaction is already being processed, cannot perform two transactions simultaneously.');
			this._doingTransaction = true;
			return {
				commit: lang.hitch(this, this._commitTransactions),
				abort: lang.hitch(this, this._abortTransactions)
			};
		},

		_noEvents: false,
		onChange: function() {
			// event stub
		}
	});

	// internal dict of static module store references
	var _moduleStores = {};

	return function(/*String*/ idProperty, /*String*/ storePath, /*String?*/ moduleFlavor) {
		// summary:
		//		Returns (and if necessary creates) a singleton instance of store.UmcpModuleStore
		//		for the given path to the store and (if specified) the given flavor.
		// idProperty: String
		//		Indicates the property to use as the identity property.
		//		The values of this property need to be unique.
		// storePath: String?
		//		UMCP URL of the module where query, set, remove, put, and add
		//		methods can be found. By default this is the module ID.
		// moduleFlavor: String?
		//		Specifies the module flavor which may need to be communicated to
		//		the server via `umc.tool.umcpCommand()`.
		//		(Is specified automatically.)

		// create a singleton for the module store for each flavor; this is to ensure that
		// the correct flavor of the module is send to the server
		var key = storePath + '@' + (moduleFlavor || 'default');
		if (!_moduleStores[key]) {
			// the store does not exist, we need to create a new singleton
			_moduleStores[key] = new _UmcpModuleStore({
				idProperty: idProperty,
				storePath: storePath,
				umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
					return tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || moduleFlavor );
				}
			});
		}
		return _moduleStores[key];
	};
});

