/*
 * SPDX-FileCopyrightText: 2019-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/when",
	"umc/widgets/ComboBox"
], function(declare, lang, when, ComboBox) {
	return declare("umc.widgets.SuggestionBox", [ ComboBox ], {
		_isValidSubset: function() {
			return true;
		},

		_setValueAttr: function(value, priorityChange, displayedValue, item) {
			if (value) {
				var origArgs = arguments;
				when(this.store.get(value), lang.hitch(this, function(item) {
					if (!item) {
						this.store.newItem({
							id: value,
							label: value,
							$dontShowInResultList: true
						});
						this.store.save();
					}
					this.inherited(origArgs);
				}));
			} else {
				this.inherited(arguments);
			}
		},

		_callbackSetLabel: function(result, query, options, priorityChange) {
			if (!result.length && query && query[this.searchAttr]) {
				this.set('value', query[this.searchAttr]);
			} else {
				this.inherited(arguments);
			}
		},

		_openResultList: function(results, query, options) {
			results = results.filter(function(i) {
				return !i.$dontShowInResultList; // $dontShowInResultList is actually an array that holds a boolean but we can just check if $dontShowInResultList is set at all
			});
			this.inherited(arguments);
		}
	});
});

