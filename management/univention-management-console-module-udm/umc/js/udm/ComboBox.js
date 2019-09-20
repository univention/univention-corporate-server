/*
 * Copyright 2012-2019 Univention GmbH
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
/*global define,require,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojo/on",
	"dojo/keys",
	"dojo/dom-construct",
	"dojo/dom-style",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, when, on, keys, domConstruct, domStyle, Deferred, tools, ComboBox, _) {
	return declare("umc.modules.udm.ComboBox", [ ComboBox ], {
		// summary:
		//		This class extends the normal ComboBox in order to encapsulate
		//		some UDM specific behavior.

		advancedSearchItem: null,

		advancedSearchString: '__advanced_search__',

		_lastSearch: null,

		_totalSize: null,

		threshold: undefined, // set by udm description properties

		dynamicValuesInfo: 'udm/syntax/choices/info',

		_state: 'waiting',

		_currentNode: null,

		_searchNode: null,

		_searchingNode: null,

		_tooManyDeferred: null,

		_setValueDeferred: null,

		_loadValues: function() {
			if (this._state == 'normal') {
				this.inherited(arguments);
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._tooManyDeferred = new Deferred();
			this._setValueDeferred = new Deferred();
		},

		_emptyStore: function() {
			delete this.store;
			this.set('store', this._createStore());
		},

		_getValueAttr: function() {
			if (this._state == 'normal') {
				return this.inherited(arguments);
			}
			// return initialValue until setValue is executed
			// at least once.
			if (!this._setValueDeferred.isFulfilled()) {
				return this._initialValue || '';
			} else {
				return this.inherited(arguments);
			}
		},

		_setValueAttr: function(newVal) {
			// save arguments, otherwise those of function(too_many) are used
			var original_arguments = arguments;
			this.inherited(arguments);
			this._tooManyDeferred.then(lang.hitch(this, function(too_many) {
				// behave normally if:
				// * all values are loaded (should be included in the third *, but i test it nonetheless
				// * no value is selected (user entered something in the combobox)
				// * item is already in list
				if (too_many && this._state != 'normal' && newVal !== '' && !this.store._getItemByIdentity(newVal)) {
					this._changeState('searching');
					this.umcpCommand('udm/syntax/choices/key', this.getParams({key: newVal})).then(lang.hitch(this, function(data) {
						this._emptyStore();
						array.forEach(data.result, lang.hitch(this, function(item) {
							this.store.newItem(item);
						}));
						if (data.result.length == this._totalSize) {
							// everything is loaded now, no need to reload anymore
							this._changeState('normal');
						} else {
							this._changeState('waiting');
							this._addAdvancedSearchItemAndSaveStore();
						}
						this.inherited(original_arguments);
						this._setValueDeferred.resolve();
						this._lastSearch = this.get('displayedValue');
					}),
					lang.hitch(this, function() {
						this._changeState('waiting');
					}));
				}
			}));
		},

		_checkThreshold: function() {
			var func = tools.stringOrFunction(this.dynamicValuesInfo, this.umcpCommand);
			return func(this.getParams()).then(function(result) {
				return result;
			});
		},

		postCreate: function() {
			this.inherited(arguments);

			// new nodes (replacing the original arrow)
			// if needed
			this._currentNode = this._buttonNode;
			this._searchNode = lang.clone(this._buttonNode);
			domStyle.set(this._searchNode.firstElementChild, {
				'backgroundPosition': '-260px -40px'
			});
			this.own(on(this._searchNode, 'click', lang.hitch(this, '_searchDisplayedValueOnServerAndOpen')));
			this._searchingNode = lang.clone(this._searchNode);
			domStyle.set(this._searchingNode.firstElementChild, {
				'background': lang.replace('url({0})', [require.toUrl('dijit/themes/umc/form/images/loading.gif')]),
				'backgroundSize': 'contain'
			});

			if (!this.depends) {
				this._checkThreshold().then(lang.hitch(this, function(result) {
					this._sizeLimitExceeded = result.size_limit_exceeded;
					this._totalSize = result.size;
					if (this._totalSize <= this.threshold) {
						this._behaveNormally();
					} else {
						this._addAdvancedSearchItemAndSaveStore();
						// handles especially for this widget:
						// ENTER: search on server
						// KEY_UP: show search icon
						// BLUR (lose focus): search on server
						// ADVANCED_SEARCH selected: show search icon
						//
						// These handles are removed as soon as _state changes
						// to normal. Then, everything works as if it was a normal ComboBox.
						this._keyPressHandle = this.on('keypress', lang.hitch(this, '_keyPress'));
						this._keyUpHandle = this.on('keyup', lang.hitch(this, '_keyUp'));
						this._validOptionHandle = this.on('blur', lang.hitch(this, '_validOption'));
						this._changeHandle = this.on('change', lang.hitch(this, function(newVal) {
							if (newVal == this.advancedSearchString) {
								if (this._state == 'waiting') {
									this._changeState('ready_to_search');
								}
								this.set('displayedValue', '');
							}
						}));
						this._tooManyDeferred.resolve(true);
						// we wait until the info command has been sent ... the user will
						// during a request see a waiting animation
						if (this._initialValue) {
							this.set('value', this._initialValue);
							this._setValueDeferred.then(lang.hitch(this, function() {
								this._readyDeferred.resolve();
							}));
						} else {
							this._readyDeferred.resolve();
						}
					}
				}));
			} else {
				this._behaveNormally();
			}
		},

		isValid: function() {
			var ret = this.inherited(arguments);
			if (ret) {
				ret = this.get('value') != this.advancedSearchString;
			}
			return ret;
		},

		_keyPress: function(evt) {
			if (evt.keyCode == keys.ENTER) {
				this._searchDisplayedValueOnServerAndOpen();
				// don't submit form
				evt.preventDefault();
			}
		},

		_keyUp: function(evt) {
			if (evt.keyCode != keys.ENTER) {
				var displayedValue = this.get('displayedValue');
				if (displayedValue === this._lastSearch) {
					this._changeState('waiting');
				} else {
					this._changeState('ready_to_search');
				}
			}
		},

		_validOption: function() {
			// if widget has a value, it should be okay
			if (!this.get('value') || this.get('value') !== this.advancedSearchString) {
				this._searchDisplayedValueOnServer();
			}
		},

		_changeState: function(new_state) {
			if (this._state == new_state) {
				return;
			}
			if (new_state == 'normal' && this._keyPressHandle) {
				// remove special handles, now it should behave like a normal combobox
				this._keyPressHandle.remove();
				this._keyUpHandle.remove();
				this._validOptionHandle.remove();
				this._changeHandle.remove();
			}
			if (new_state == 'normal' || new_state == 'waiting') {
				// works even if new_node == old_node
				domConstruct.place(this._buttonNode, this._currentNode, 'replace');
				this._currentNode = this._buttonNode;
			} else if (new_state == 'ready_to_search') {
				domConstruct.place(this._searchNode, this._currentNode, 'replace');
				this._currentNode = this._searchNode;
			} else if (new_state == 'searching') {
				domConstruct.place(this._searchingNode, this._currentNode, 'replace');
				this._currentNode = this._searchingNode;
			} else {
				console.warn(new_state + ' is not defined as a state');
			}
			this._state = new_state;
		},

		_searchDisplayedValueOnServerAndOpen: function() {
			return this._searchDisplayedValueOnServer(true);
		},

		_searchDisplayedValueOnServer: function(open) {
			var deferred = new Deferred();
			when(this._searchOnServer(this.get('displayedValue')), lang.hitch(this, function() {
				if (open) {
					this.loadAndOpenDropDown();
				}
				deferred.resolve();
			}));
			return deferred;
		},

		_searchOnServer: function(search_value) {
			if (search_value === this._lastSearch || search_value === '') {
				this._changeState('waiting');
				return null;
			}
			if (this._state == 'ready_to_search' || this._state == 'waiting') {
				var deferred = new Deferred();
				var func = tools.stringOrFunction(this.dynamicValues, this.umcpCommand);
				var params = this.getParams({
					objectPropertyValue: search_value,
					objectProperty: 'None'
				});
				this.closeDropDown();
				this._changeState('searching');
				func(params).then(lang.hitch(this, function(result) {
					this._emptyStore();
					result.sort(tools.cmpObjects({
						attribute: 'label',
						ignoreCase: true
					}));
					var value = this.get('displayedValue');
					var value_selected;
					array.forEach(result, lang.hitch(this, function(item) {
						if (item.label === value) {
							value_selected = item.id;
						}
						this.store.newItem(item);
					}));
					if (value_selected !== undefined) {
						this.set('value', value_selected);
					}
					if (result.length == this._totalSize) {
						// everything is loaded now, no need to reload anymore
						this._changeState('normal');
					} else {
						this._addAdvancedSearchItemAndSaveStore(value_selected === undefined);
						this._changeState('waiting');
					}
					this._lastSearch = search_value;
					deferred.resolve();
				}),
				lang.hitch(this, function() {
					this._changeState('waiting');
					deferred.resolve();
				}));
				return deferred;
			}
		},

		_addAdvancedSearchItemAndSaveStore: function() {
			if (this.advancedSearchItem === null) {
				this.advancedSearchItem = {};
				this.advancedSearchItem.id = this.advancedSearchString;
				var detail;
				if (this._sizeLimitExceeded) {
					detail = _('number exceeded configured limit');
				} else {
					detail = lang.replace(_('in {size} objects'), {size: this._totalSize});
				}
				this.advancedSearchItem.label = _('Advanced Search') + ' (' + detail + ')';
			}
			this.store.newItem(this.advancedSearchItem);
		},

		_behaveNormally: function() {
			this._changeState('normal');
			on.once(this, 'valuesloaded', lang.hitch(this, function() {
				this._tooManyDeferred.resolve(false);
			}));
			this._loadValues();
		},

		getParams: function(params) {
			params = params || {};
			if (this.dynamicOptions) {
				if (typeof this.dynamicOptions == "function") {
					lang.mixin(params, this.dynamicOptions(params));
				}
				else if (typeof this.dynamicOptions == "object") {
					lang.mixin(params, this.dynamicOptions);
				}
			}
			return params;
		}

	});
});

