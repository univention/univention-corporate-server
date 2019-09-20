/*
 * Copyright 2013-2019 Univention GmbH
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

		preloadModuleInformation: function() {
			var isPolicyModule = this.superModule.indexOf('policies/') === 0;
			if (isPolicyModule) {
				// preloading layout information cannot be done for policies as
				// referring objects are rendered into the layout, as well, and
				// thus the object DN needs to be sent to the server
				return;
			}

			this.getMetaInfo(this.superModule);
			this.getContainers(this.superModule);
			this.getChildModules().then(lang.hitch(this, function(modules) {
				this._loadPropertiesMulti(modules);
				this._loadLayoutMulti(modules);
				this._loadPoliciesMulti(modules);
				this._loadWizardMulti(modules);
			}));
		},

		getChildModules: function(superordinate, container, asIdLabelPair) {
			superordinate = superordinate || null;
			container = container || null;
			var result = this._get('childModules', superordinate, container);
			if (result) {
				if (asIdLabelPair) {
					return result;
				}
				return result.then(_idLabelPair2Id);
			}

			result = tools.umcpCommand('udm/types', {
				superordinate: superordinate,
				container: container
			}, true, this.superModule).then(lang.hitch(this, function(response) {
				if (!response.result.length) {
					// has no sub modules
					return [{
						id: this.superModule,
						label: ''
					}];
				}
				return response.result;
			}));

			this._set(result, 'childModules', superordinate, container);
			if (asIdLabelPair) {
				return result;
			}
			return result.then(_idLabelPair2Id);
		},

		getWizard: function(module) {
			var result = this._get('wizard', module);
			if (result) {
				return result;
			}

			var wizardModuleURL = 'umc/modules/udm/wizards/' + (module || this.superModule);
			var deferred = new Deferred();
			deferred.then(null, function() {});
			tools.urlExists(wizardModuleURL + '.js').then(
				lang.hitch(this, function() {
					require([wizardModuleURL], lang.hitch(this, function(WizardClass) {
						deferred.resolve(WizardClass);
					}));
				}),
				lang.hitch(this, function() {
					deferred.reject();
				})
			);

			this._set(deferred, 'wizard', module);
			return deferred;
		},

		_loadWizardMulti: function(modules) {
			array.forEach(modules, function(imodule) {
				this.getWizard(imodule);
			}, this);
		},

		_getInfo: function(udmCommand, udmOptions, flavor, module, forceLoad) {
			module = module || this.superModule;

			// extend the cache arguments with the additional UDM option values
			// ... make sure that the key order is stable
			var keys = [];
			tools.forIn(udmOptions, function(ikey, ival) {
				keys.push(ikey);
			});
			keys.sort();

			var args = [udmCommand, module];
			array.forEach(keys, function(ikey) {
				args.push(udmOptions[ikey]);
			});
			var result = this._get.apply(this, args);
			if (result && !forceLoad) {
				return result;
			}

			// perform UDM command
			var params = lang.mixin({
				objectType: module
			}, udmOptions || {});
			result = tools.umcpCommand('udm/' + udmCommand, params, true, flavor).then(function(response) {
				return response.result;
			});

			args.unshift(result);
			this._set.apply(this, args);
			return result;
		},

		getMetaInfo: function(module, forceLoad) {
			return this._getInfo('meta_info', {}, this.superModule, module, forceLoad);
		},

		getContainers: function(module, forceLoad) {
			return this._getInfo('containers', {}, this.superModule, module, forceLoad);
		},

		getValues: function(module, property, forceLoad) {
			return this._getInfo('values', {
				objectProperty: property || null
			}, this.superModule, module, forceLoad);
		},

		getReports: function(module, forceLoad) {
			module = module || this.superModule;
			return this._getInfo('reports/query', {}, module, module, forceLoad);
		},

		getTemplates: function(module, forceLoad) {
			return this._getInfo('templates', {}, this.superModule, module, forceLoad);
		},

		_getInfos: function(infoType, modules, objDN, forceLoad) {
			// see whether information for all modules have already been cached
			var allInfo = array.map(modules, function(imodule) {
				return this._get(infoType, imodule);
			}, this);
			var allInfoLoaded = array.every(allInfo, function(i) {
				return i;
			});
			var isPolicyModule = this.superModule.indexOf('policies/') === 0;
			// The referencing objects for a policies/* object are only in
			// the layout if an objectDN was provided.
			// - When adding a new policies/* object the "Referencing objects"
			// tab is/should not be shown -
			// This causes the issue that when for example a policies/pwhistory
			// object is added the layout without the referencing objects is cached.
			// When after that the detailpage for a policies/pwhistory is opened
			// the cached layout is used and no referencing objects tab is shown.
			// Or the same issue in reverse: First detailpage -> layout with referencing objects
			// cached. sTthen adding new object of same type -> referencing objects tab is shown
			// instead of being hidden. Do not return cached values for polcies/* types (Bug #38674)
			if (!isPolicyModule && allInfoLoaded && !forceLoad) {
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
			var ret = tools.umcpCommand('udm/' + infoType, types, true, this.superModule).then(lang.hitch(this, function(response) {
				// resolve Deferreds in cache
				array.forEach(response.result, function(ires, idx) {
					var imodule = modules[idx];
					var deferred = this._get(infoType, imodule);
					deferred.resolve(ires);
				}, this);
			}));

			// return array of Deferreds
			return array.map(modules, function(imodule) {
				return this._get(infoType, imodule);
			}, this);
		},

		getProperties: function(module, objDN, forceLoad) {
			return this._getInfos('properties', [module], objDN, forceLoad)[0];
		},

		_loadPropertiesMulti: function(modules) {
			this._getInfos('properties', modules, null, false);
		},

		getLayout: function(module, objDN, forceLoad) {
			return this._getInfos('layout', [module], objDN, forceLoad)[0];
		},

		_loadLayoutMulti: function(modules) {
			this._getInfos('layout', modules, null, false);
		},

		getPolicies: function(module, forceLoad) {
			return this._getInfos('policies', [module], null, forceLoad)[0];
		},

		_loadPoliciesMulti: function(modules) {
			this._getInfos('policies', modules, null, false);
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



