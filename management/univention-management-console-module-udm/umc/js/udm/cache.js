/*
 * Copyright 2013 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/declare",
	"dojo/Deferred",
	"umc/tools"
], function(lang, array, declare, Deferred, tools) {
	var _toIndexStr = function(args, offset) {
		var str = '';
		for (var i = offset; i < args.length; ++i) {
			str += args[i] + '#';
		}
		return str;
	};

	var _idLabelPair2Id = function(items) {
		return array.map(items, function(i) {
			return i.id;
		});
	};

	var _isPolicy = function(module) {
		return module.indexOf('policies/') == 0;
	};

	var _Cache = declare([], {
		superModule: null,
		_cache: null,

		constructor: function(props) {
			lang.mixin(this, props);
			this.reset();
		},

		reset: function() {
			this._cache = {};
		},

		_get: function() {
			var indexStr = _toIndexStr(arguments, 0);
			return this._cache[indexStr];
		},

		_set: function(data) {
			var indexStr = _toIndexStr(arguments, 1);
			this._cache[indexStr] = data;
		},

		getChildModules: function(asIdLabelPair) {
			var result = this._get('childModules', this.superModule);
			if (result) {
				if (asIdLabelPair) {
					return result;
				}
				return result.then(_idLabelPair2Id);
			}

			result = tools.umcpCommand('udm/types', {}, true, this.superModule).then(lang.hitch(this, function(response) {
				if (!response.result.length) {
					// has no sub modules
					return [{
						id: this.superModule,
						label: ''
					}];
				}
				return response.result;
			}));

			this._set(result, 'childModules', this.superModule);
			return result.then(_idLabelPair2Id);
		},

		preloadModuleInformation: function() {
			if (_isPolicy(this.superModule)) {
				// preloading layout information cannot be done for policies as
				// referring objects are rendered into the layout, as well, and
				// thus the object DN needs to be sent to the server
				return;
			}

			this.getChildModules().then(lang.hitch(this, function(modules) {
				this._loadPropertiesMulti(modules, true);
				this._loadLayoutMulti(modules, true);
				this._loadPoliciesMulti(modules, true);
			}));
		},

		_getInfos: function(infoType, modules, objDN, forceLoad) {
			// see whether information for all modules have already been cached
			var allInfo = array.map(modules, function(imodule) {
				return this._get(infoType, imodule);
			}, this);
			var allInfoLoaded = array.every(allInfo, function(i) {
				return i;
			});
			if (allInfoLoaded && !forceLoad) {
				// return the cached information
				return allInfo;
			}

			// prepare Deferreds for each module
			array.forEach(modules, function(imodule) {
				this._set(new Deferred(), infoType, imodule);
			}, this);

			// load information
			var types = array.map(modules, function(imodule) {
				return {
					objectType: imodule,
					objectDN: objDN
				};
			});
			return tools.umcpCommand('udm/' + infoType, types, true, this.superModule).then(lang.hitch(this, function(response) {
				// resolve Deferreds in cache
				array.forEach(response.result, function(ires, idx) {
					var imodule = modules[idx];
					var deferred = this._get(infoType, imodule);
					deferred.resolve(ires);
				}, this);

				return response.result;
			}));
		},

		getProperties: function(module, objDN) {
			return this._getInfos('properties', [module], objDN, false)[0];
		},

		_loadPropertiesMulti: function(modules, forceLoad) {
			this._getInfos('properties', modules, null, forceLoad);
		},

		getLayout: function(module, objDN) {
			return this._getInfos('layout', [module], objDN, false)[0];
		},

		_loadLayoutMulti: function(modules, forceLoad) {
			this._getInfos('layout', modules, null, forceLoad);
		},

		getPolicies: function(module) {
			return this._getInfos('policies', [module], null, false)[0];
		},

		_loadPoliciesMulti: function(modules, forceLoad) {
			this._getInfos('policies', modules, null, forceLoad);
		}
	});

	var _superCache = {};
	return {
		get: function(superModule) {
			if (superModule in _superCache) {
				return _superCache[superModule];
			}
			var cache = new _Cache({
				superModule: superModule
			});
			_superCache[superModule] = cache;
			return cache;
		},

		reset: function(/*String?*/ superModule) {
			if (!superModule) {
				tools.forIn(_superCache, function(imodule, icache) {
					icache.reset();
				});
			} else if (superModule in _superCache) {
				_superCache[superModule].reset();
			}
		}
	};
});



