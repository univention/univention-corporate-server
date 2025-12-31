/*
 * SPDX-FileCopyrightText: 2022-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/widgets/SuggestionBox",
	"umc/i18n!"
], function(declare, lang, SuggestionBox, _) {
	return declare("umc.widgets.MailBox", [ SuggestionBox ], {
		// This widget only works if the domain items (set by staticValues, dynamicValues...)
		// have the same id and label.
		// e.g.
		// {
		//   id: 'example.com',
		//   label: 'example.com',
		// }

		value: '',

		placeHolder: _('mail@example.org'),

		_setValueAttr: function(value, priorityChange, displayedValue, item) {
			if (value) {
				var origArgs = arguments;
				this.store.get(value).then(lang.hitch(this, function(item) {
					// if the set value is a store value,
					// which happens when e.g. an item in the dropdown is selected,
					// then 'value' is the id of that store item which is only the domain - e.g. example.com.
					// But we want value to be the label of that store item, which is adjusted in _startSearch.
					if (item) {
						// modify origArgs
						value = this.item2object(item).label;
					}
					this.inherited(origArgs);
				}));
			} else {
				this.inherited(arguments);
			}
		},

		_startSearchFromInput: function() {
			// dijit/form/_AutoCompleterMixin.js
			this.item = undefined; // undefined means item needs to be set

			this._startSearch(this.focusNode.value, true);
		},

		_startSearch: function(text, fromKeyboardInput) {
			// when text is inputted into the textbox we want
			// to adjust the labels of the store items
			// to be the local part (before the '@' sign) of the inputted text
			// plus the domain label from the store items.
			var localPart = this.textbox.value.split('@')[0];
			this.store.query().then(lang.hitch(this, function(items) {
				items.forEach(lang.hitch(this, function(item) {
					var domain = this.store.getValue(item, 'id');
					this.store.setValue(item, 'label', localPart + '@' + domain);
				}));
			}));

			if (fromKeyboardInput) {
				if (this.textbox.value.includes('@')) {
					this.inherited(arguments);
				} else {
					this.closeDropDown();
				}
			} else {
				this.inherited(arguments);
			}
		}
	});
});

