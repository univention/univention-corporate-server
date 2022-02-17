/*
 * Copyright 2022 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/widgets/SuggestionBox",
	"umc/i18n!"
], function(declare, lang, SuggestionBox, _) {
	return declare("umc.widgets.MailBox", [ SuggestionBox ], {
		value: '',

		placeHolder: _('mail@example.com'),

		_setValueAttr: function(value, priorityChange, displayedValue, item) {
			if (value) {
				var origArgs = arguments;
				this.store.get(value)
					.then(lang.hitch(this, function(item) {
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
			this._startSearch(this.focusNode.value, true);
		},

		_startSearch: function(text, fromKeyboardInput) {
			// when text is inputted into the textbox we want
			// to adjust the labels of the store items
			// to be the local part (before the '@' sign) of the inputted text
			// plus the domain label from the store items.
			var localPart = this.textbox.value.split('@')[0];
			this.store.query()
				.then(lang.hitch(this, function(items) {
					items.forEach(lang.hitch(this, function(item) {
						var domain = this.store.getValue(item, 'domain');
						if (!domain) {
							domain = this.store.getValue(item, 'label');
							this.store.setValue(item, 'domain', domain);
						}
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
		},
	});
});

