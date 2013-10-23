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
/*global define require console */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/has",
	"dojo/dom-class",
	"dojo/regexp",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TextBox",
	"umc/widgets/LabelPane",
	"umc/widgets/Button",
	"umc/i18n!umc/branding,umc/app"
], function(declare, lang, array, has, domClass, regexp, ContainerWidget, TextBox, LabelPane, Button, _) {
	return declare("umc.widgets.LiveSearchSidebar", [ContainerWidget], {
		// summary:
		//		Offers a side bar for live searching, a set of categories can be defined.
		//		This class is used in the UMC overview and the App Center.

		// categories: Object[]|String[]
		// 		Array of categories exposing at least the fields 'id' and 'label'
		// 		or array of strings.
		categories: null,

		_categoriesAsIdLabelPairs: true,

		// category: Object|String
		//		Reference to the currently selected category
		category: null,

		// category: Object|String
		//		Reference to the 'all' category
		allCategory: null,

		baseClass: 'umcLiveSearchSidebar',

		style: 'overflow: auto;',

		// searchableAttributes: String[]
		//		Array of strings that shall be searched.
		//		defaults to ['name', 'description', 'categories', 'keywords']
		searchableAttributes: null,

		buildRendering: function() {
			this.inherited(arguments);
			if (this.searchableAttributes === null) {
				this.searchableAttributes = ['name', 'description', 'categories', 'keywords'];
			}

			this._searchTextBox = new TextBox({
				inlineLabel: _('Search term'),
				style: 'width: 135px;'
			});
			this.addChild(this._searchTextBox);

			this._categoryContainer = new ContainerWidget({});
			this.addChild(this._categoryContainer);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._searchTextBox.on('keyup', lang.hitch(this, function() {
				this._updateCss(); // ... just to be sure
				this.onSearch();
			}));
		},

		_getUniformCategory: function(category) {
			if (typeof category == 'string') {
				this._categoriesAsIdLabelPairs = false;
				return { id: category, label: category };
			}
			return category;
		},

		_isInSearchMode: function() {
			return Boolean(lang.trim(this.get('value')));
		},

		_getValueAttr: function() {
			return this._searchTextBox.get('value');
		},

		_setValueAttr: function(value) {
			return this._searchTextBox.set('value', value);
		},

		_getCategoryAttr: function() {
			var category = this.category;
			if (this._isInSearchMode() && this.allCategory) {
				// in search mode, the current category is always the "all" category
				category = this._getUniformCategory(this.allCategory);
			}
			if (!this._categoriesAsIdLabelPairs) {
				return category.id;
			}
			return category;
		},

		_setCategoryAttr: function(_category) {
			this._set('category', this._getUniformCategory(_category));
			this._updateCss();
			this.onSearch();
			if (!has('touch')) {
				this._searchTextBox.focus();
			}
		},

		_clearCategoryNodes: function() {
			array.forEach(this._categoryContainer.getChildren(), lang.hitch(this, function(category) {
				this._categoryContainer.removeChild(category);
				category.destroyRecursive();
			}));
		},

		_setCategoriesAttr: function(categories) {
			this._clearCategoryNodes();

			// add one node elements for each category
			array.forEach(categories, lang.hitch(this, function(_category) {
				var category = this._getUniformCategory(_category);
				this._categoryContainer.addChild(new Button({
					label: category.label,
					_categoryID: category.id,
					callback: lang.hitch(this, function() {
						this.set('value', '');
						this.set('category', category);
					})
				}));
			}));

			this._set('categories', categories);

			// preselect the first category
			this.set('category', categories[0]);
		},

		_updateCss: function() {
			var categories = this._categoryContainer.getChildren();
			var currentCategory = this._getUniformCategory(this.get('category'));
			array.forEach(categories, lang.hitch(this, function(ibutton) {
				var isSelected = (currentCategory && currentCategory.id == ibutton._categoryID) || (!currentCategory && ibutton._categoryID == '$all$');
				domClass.toggle(ibutton.domNode, 'umcCategorySelected', isSelected);
			}));
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
				test: function(value, obj) {
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
		},

		focus: function() {
			this._searchTextBox.focus();
		},

		onSearch: function() {
			// event stub
		}
	});
});

