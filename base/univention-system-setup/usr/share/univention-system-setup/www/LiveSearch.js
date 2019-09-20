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
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/event",
	"dojo/dom-construct",
	"dojo/dom-class",
	"dojo/on",
	"dojo/keys",
	"dojo/topic",
	"dojox/html/styles",
	"dijit/form/ComboBox",
	"umc/widgets/TextBox",
	"umc/i18n!setup"
], function(declare, lang, dojoEvent, domConstruct, domClass, on, keys, topic, styles, DijitComboBox, TextBox, _) {
	return declare('umc.modules.setup.LiveSearch', [DijitComboBox, TextBox], {
		searchAttr: 'label',
		hasDownArrow: false,
		autoComplete: false,
		highlightMatch: 'none',
		'class': 'umcLiveSearch',
		store: null,
		_searchNode: null,
		_searchingNode: null,
		_currentNode: null,
		inlineLabel: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._currentNode = this._buttonNode;

			this._searchNode = lang.clone(this._buttonNode);
			this._searchNode.style.display = '';
			this.own(on(this._searchNode, 'click', lang.hitch(this, 'loadDropDown')));

			this._searchingNode = lang.clone(this._searchNode);
			domClass.add(this._searchingNode, 'umcLiveSearching');

			this._setState('search');
		},

		postCreate: function() {
			this.inherited(arguments);

			this.store.on('searching', lang.hitch(this, '_setState', 'searching'));
			this.store.on('searchFinished', lang.hitch(this, '_setState', 'search'));
		},

		_setState: function(state) {
			var newNode = this._currentNode;
			if (state == 'searching') {
				newNode = this._searchingNode;
			}
			else {
				newNode = this._searchNode;
			}
			domConstruct.place(newNode, this._currentNode, 'replace');
			this._currentNode = newNode;
		},

		loadDropDown: function() {
			this._startSearch(this.get('value'));
		},

		_autoSelect: function() {
			var lastResult = this.store.lastResult;
			if (this.state != 'searching' && lastResult.length && this._opened && !this.dropDown.selected) {
				// select first item
				this.set('item', lastResult[0]);
				this.closeDropDown();
				return true;
			}
			return false;
		},

		_onBlur: function(evt) {
			this._autoSelect();
			this.inherited(arguments);
		},

		_onKey: function(evt) {
			if (evt.keyCode == keys.ENTER) {
				var selected = this._autoSelect();
				if (selected || this.state == 'searching' || !this.get('item')) {
					// stop processing key event
					dojoEvent.stop(evt);
					return;
				}
			}
			if (evt.keyCode == keys.TAB) {
				// when pressing tab key, auto select the first entry from result list
				// and continue processing event
				this._autoSelect();
			}
			this.inherited(arguments);
		}
	});
});
