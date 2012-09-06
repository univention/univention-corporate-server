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
/*global console dojo dojox dijit umc */

dojo.provide("umc.modules._packages.store");

dojo.require("umc.tools");
dojo.require("dojo.DeferredList");
dojo.require("dojo.store.util.QueryResults");
dojo.require("dojo.store.Observable");
dojo.require("dojo.store.Memory");
dojo.require("dojo.data.ObjectStore");


umc.modules._packages.store._moduleStores = {};

umc.modules._packages.store.getModuleStore = function(/*String*/ idProperty, /*String*/ storePath, /*String?*/ moduleFlavor) {
	var stores = dojo.getObject('umc.modules._packages.store._moduleStores', true);
	var key = storePath + '@' + (moduleFlavor || 'default');
	if (!stores[key]) {
		stores[key] = dojo.store.Observable(new umc.modules._packages.store.UmcpModuleStore({
			idProperty: idProperty,
			storePath: storePath,
			umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
				return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || moduleFlavor );
			}
		}));
	}
	return stores[key];
};

dojo.declare("umc.modules._packages.store.Memory", dojo.store.Memory, {

	onChange: function() {
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

dojo.declare("umc.modules._packages.store.UmcpModuleStore", null, {
	idProperty: '',

	storePath: '',

	umcpCommand: umc.tools.umcpCommand,

	constructor: function(params) {
		dojo.mixin(this, params);
	},

	getIdentity: function(object) {
		return object[this.idProperty];
	},

	_genericCmd: function(type, param) {
		// console.log('_genericCmd: ' + dojo.toJson(arguments));
		if (this._doingTransaction) {
			this._addTransactions(type, [param]);
		}
		else {
			return this._genericMultiCmd(type, [param]).
				then(function(results) {
					if (results) {
						/*
						 * BEGIN CHANGED
						 * return 400 if results is an object
						 * as returned from backend-sanitizers
						 */
						if (dojo.isArray(results)) {
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
					}
				});
		}
	},

	_genericMultiCmd: function(type, params) {
		// console.log('_genericMultiCmd: ' + dojo.toJson(arguments));
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
				then(dojo.hitch(this, function(data) {
					var res = dojo.getObject('result', false, data);

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
		umc.tools.forIn(_query, function(ikey, ival) {
			query[ikey] = (dojo.isString(ival) || typeof ival == 'boolean' || 'null' === ival) ? ival : String(ival);
			++nQueryEl;
		}, this, true);
		var deferred = new dojo.Deferred();
		if (nQueryEl) {
			deferred = this.umcpCommand(this.storePath + '/query', query);
			deferred = deferred.then(function(data) {
				var result = data.result;
				var sort = dojo.getObject('sort', false, options);
				if (sort) {
					result.sort(umc.tools.cmpObjects(sort));
				}
				return result;
			});
		}
		else {
			deferred.callback([]);
		}
		return dojo.store.util.QueryResults(deferred);
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
		var deferred = new dojo.Deferred();
		deferred.resolve();
		var results = [];
		this._doingTransaction = false;
		this._noEvents = true; // switch off event notifications
		var dataModified = false;
		dojo.forEach(this._groupedTransactions, dojo.hitch(this, function(igroup, i) {
			dataModified = dataModified || 'remove' == igroup.type || 'put' == igroup.type || 'add' == igroup.type;

			deferred = deferred.then(dojo.hitch(this, function(data) {
				return this._genericMultiCmd(igroup.type, igroup.params).then(function(data) {
					results = results.concat(data);
					return null;
				});
			}));
		}));

		var _cleanup = dojo.hitch(this, function() {
			this._noEvents = false;
			if (dataModified) {
				this.onChange();
			}

			this._groupedTransactions = [];

		});

		deferred = deferred.then(dojo.hitch(this, function() {
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
		umc.tools.assert(!this._doingTransaction, 'Another UMCP transaction is already being processed, cannot perform two transactions simultaneously.');
		this._doingTransaction = true;
		return {
			commit: dojo.hitch(this, this._commitTransactions),
			abort: dojo.hitch(this, this._abortTransactions)
		};
	},

	_noEvents: false,
	onChange: function() {
	}
});


