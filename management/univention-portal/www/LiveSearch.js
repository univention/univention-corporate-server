/*
 * Copyright 2017-2019 Univention GmbH
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
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/mouse",
	"dojo/regexp",
	"umc/widgets/ContainerWidget",
	"umc/widgets/SearchBox",
	"umc/i18n!"
], function(declare, lang, array, domClass, mouse, regexp, ContainerWidget, SearchBox, _) {
	return declare("PortalLiveSearch", [ContainerWidget], {
		// summary:
		//		Offers a text box for live searching.
		//		This class is used in the UMC overview and the App Center.

		searchLabel: null,

		// searchableAttributes: String[]
		//		Array of strings that shall be searched.
		//		defaults to ['name', 'description', 'categories', 'keywords']
		searchableAttributes: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass = 'portalLiveSearch';

			var _searchableAttributes = ['name', 'description', 'categories', 'keywords'];
			this.searchableAttributes = this.searchableAttributes || _searchableAttributes;
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._searchTextBox = new SearchBox({
				inlineLabel: this.searchLabel || _('Search term')
			});
			this.addChild(this._searchTextBox);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._searchTextBox.on('keyup', lang.hitch(this, 'search'));
			this._searchTextBox.on('focus', lang.hitch(this, 'onFocus'));
			this._searchTextBox.on('blur', lang.hitch(this, 'onBlur'));
		},

		expandSearch: function() {
			if (this.get('disabled')) {
				return;
			}
			domClass.remove(this.domNode, 'portalLiveSearch--collapsed');
		},

		collapseSearch: function(ignoreFocus) {
			// var shouldCollapse = (ignoreFocus || !this.focused) && !this.get('value');
			// domClass.toggle(this.domNode, 'portalLiveSearch--collapsed', shouldCollapse);
			domClass.add(this.domNode, 'portalLiveSearch--collapsed');
		},

		_setDisabledAttr: function(disabled) {
			this._searchTextBox.set('disabled', disabled);
			this._set('disabled', disabled);
		},

		_getValueAttr: function() {
			return this._searchTextBox.get('value');
		},

		_setValueAttr: function(value) {
			return this._searchTextBox.set('value', value);
		},

		focus: function() {
			this._searchTextBox.focus();
		},

		blur: function() {
			this._searchTextBox.textbox.blur();
		},

		onFocus: function() {
			// event stub
		},

		onBlur: function() {
			// event stub
		},

		_lastValue: null,
		search: function() {
			// ignore empty search expect something was searched before
			// (e.g. deleting the last letter should make a new search so that everything is shown)
			var searchPattern = this.get('value');
			if (searchPattern || this._lastValue) {
				this._lastValue = searchPattern;
				this.onSearch();
			}
		},

		onSearch: function() {
			// event stub
		},

		getSearchQuery: function(searchPattern) {
			// sanitize the search pattern
			searchPattern = regexp.escapeString(searchPattern);
			searchPattern = searchPattern.replace(/\\\*/g, '.*');
			searchPattern = searchPattern.replace(/ /g, '\\s+');

			// build together the search function
			var regex  = new RegExp(searchPattern, 'i');
			var searchableAttributes = this.searchableAttributes;
			var query = {
				test: function(obj) {
					var string = '';
					array.forEach(searchableAttributes, function(attr) {
						var val = obj[attr] || '';
						if (val instanceof Array) {
							val = val.join(' ');
						}
						string += val + ' ';
					});
					return regex.test(string);
				}
			};
			return query;
		}
	});
});


