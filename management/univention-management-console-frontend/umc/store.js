/*
 * Copyright 2011 Univention GmbH
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
/*global console dojo dojox dijit umc */

dojo.provide("umc.store");

dojo.require("umc.tools");
dojo.require("dojo.DeferredList");
dojo.require("dojo.store.util.QueryResults");
dojo.require("dojo.store.Observable");
dojo.require("dojo.store.Memory");
dojo.require("dojo.data.ObjectStore");


// internal dict of static module store references
umc.store._moduleStores = {};

umc.store.getModuleStore = function(/*String*/ idProperty, /*String*/ storePath, /*String?*/ moduleFlavor) {
	// summary:
	//		Returns (and if necessary creates) a singleton instance of umc.store.UmcpModuleStore
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
	var stores = dojo.getObject('umc.store._moduleStores', true);
	var key = storePath + '@' + (moduleFlavor || 'default');
	if (!stores[key]) {
		// the store does not exist, we need to create a new singleton
		stores[key] = dojo.store.Observable(new umc.store.UmcpModuleStore({
			idProperty: idProperty,
			storePath: storePath,
			umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
				return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || moduleFlavor );
			}
		}));
	}
	return stores[key];
};

dojo.declare("umc.store.Memory", dojo.store.Memory, {
	// summary:
	//		Enhances the original Memory class with a onChange event for the Grid.

	onChange: function() {
		// event stub
	},

	put: function() {
		var res = this.inherited(arguments);
		this.onChange();
		return res;
	},

	add: function() {
		var res = this.inherited(arguments);
		this.onChange();
		return res;
	},

	remove: function() {
		var res = this.inherited(arguments);
		this.onChange();
		return res;
	},

	setData: function() {
		this.inherited(arguments);
		this.onChange();
	}
});

dojo.declare("umc.store.UmcpModuleStore", null, {
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
	umcpCommand: umc.tools.umcpCommand,

	constructor: function(params) {
		dojo.mixin(this, params);
	},

	getIdentity: function(object) {
		// summary:
		//		Returns an object's identity
		// object: Object
		//		The object to get the identity from
		//	returns: String
		//console.log('getIdentity: ' + dojo.toJson(arguments));
		return object[this.idProperty];
	},

	_genericCmd: function(type, param) {
		//console.log('_genericCmd: ' + dojo.toJson(arguments));
		if (this._doingTransaction) {
			this._addTransactions(type, [param]);
		}
		else {
			return this._genericMultiCmd(type, [param]).
				then(function(results) {
					if (results && dojo.isArray(results)) {
						return results[0];
					}
				});
		}
	},

	_genericMultiCmd: function(type, params) {
		//console.log('_genericMultiCmd: ' + dojo.toJson(arguments));
		if (this._doingTransaction) {
			this._addTransactions(type, params);
		}
		else {
			// send the UMCP command
			return this.umcpCommand(this.storePath + '/' + type, params).
				then(dojo.hitch(this, function(data) {
					// make sure that we get an non-empty array
					//console.log('# _genericMultiCmd - deferred: data=' + String(data));
					var res = dojo.getObject('result', false, data);

					// send event when changes occurred
					if (!this._noEvents && ('remove' == type || 'put' == type || 'add' == type)) {
						this.onChange();
					}

					//umc.tools.assert(res && dojo.isArray(res) && res.length == params.length,
					//	dojo.replace('UMCP result from {0}/{1} did not yield an non-empty array!', [this.storePath, type]));
					return res;
				}));
		}
	},

	get: function(id) {
		//console.log('get: ' + dojo.toJson(arguments));
		//	summary:
		//		Retrieves an object by its identity. This will trigger an UMCP request 
		//		calling the module method 'GET'.
		//	id: Number
		//		The identity to use to lookup the object
		//	returns: dojo.Deferred
		//		The object in the store that matches the given id.
		return this._genericCmd('get', id);
	},

	put: function(object, options) {
		//console.log('put: ' + dojo.toJson(arguments));
		// summary:
		//		Stores an object. This will trigger an UMCP request calling the module
		//		method 'SET'.
		// object: Object
		//		The object to store.
		// options:
		//		This parameter is currently ignored.
		// returns: dojo.Deferred
		return this._genericCmd('put', {
			object: object, 
			options: options || null
		});
	},

	add: function(object, options) {
		//console.log('add: ' + dojo.toJson(arguments));
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
		});
	},

	remove: function( object, options ) {
		//console.log('remove: ' + dojo.toJson(arguments));
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
		} );
	},

	query: function(_query, options) {
		//console.log('query: ' + dojo.toJson(arguments));
		// summary:
		//		Queries the store for objects. This will trigger a GET request to the server, with the
		//		query added as a query string.
		// query: Object
		//		The query to use for retrieving objects from the store.
		// options: 
		//		Query options, such as 'sort' (see also umc.tools.cmpObjects()).
		// returns: dojo.store.api.Store.QueryResults
		//		The results of the query, extended with iterative methods.

		// if called via dojo.data.ObjectStore, queries can be translated to regexps
		var query = {};
		var nQueryEl = 0;
		umc.tools.forIn(_query, function(ikey, ival) {
			query[ikey] = (dojo.isString(ival) || typeof ival == 'boolean' || 'null' === ival) ? ival : String(ival);
			++nQueryEl;
		}, this, true);
		var deferred = new dojo.Deferred();
		if (nQueryEl) {
			// non-empty query
			deferred = this.umcpCommand(this.storePath + '/query', query);
			deferred = deferred.then(function(data) {
				var result = data.result;
				// if requested, sort the list
				var sort = dojo.getObject('sort', false, options);
				if (sort) {
					result.sort(umc.tools.cmpObjects(sort));
				}
				return result;
			});
		}
		else {
			// empty query -> return an empty list 
			// this is the query the grid will send automatically at the beginning
			deferred.callback([]);
		}
		return dojo.store.util.QueryResults(deferred);
	},

	// _doingTransaction: Boolean
	//		Internal variable that tells user whether we are performing an transaction.
	_doingTransaction: false,

	_groupedTransactions: [],

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
		var deferred = new dojo.Deferred();
		deferred.resolve();
		var results = [];
		this._doingTransaction = false;
		this._noEvents = true; // switch off event notifications
		var dataModified = false;
		dojo.forEach(this._groupedTransactions, dojo.hitch(this, function(igroup, i) {
			// check whether the data is modified
			dataModified = dataModified || 'remove' == igroup.type || 'put' == igroup.type || 'add' == igroup.type;

			// chain all deferred commands
			deferred = deferred.then(dojo.hitch(this, function(data) {
				return this._genericMultiCmd(igroup.type, igroup.params).then(function(data) {
					results = results.concat(data);
					//console.log(dojo.replace('# deferred: i={0} data={1}', [i, String(data)]));
					return null;
				});
			}));
		}));

		var _cleanup = dojo.hitch(this, function() {
			// switch back on events and send onChange event
			this._noEvents = false;
			if (dataModified) {
				this.onChange();
			}

			// remove all transactions 
			this._groupedTransactions = [];

		});

		deferred = deferred.then(dojo.hitch(this, function() {
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
		//		`dojo.DeferredList` object for all transactions.
		umc.tools.assert(!this._doingTransaction, 'Another UMCP transaction is already being processed, cannot perform two transactions simultaneously.');
		this._doingTransaction = true;
		return {
			commit: dojo.hitch(this, this._commitTransactions),
			abort: dojo.hitch(this, this._abortTransactions)
		};
	},

	_noEvents: false,
	onChange: function() {
		// event stub
	}
});


