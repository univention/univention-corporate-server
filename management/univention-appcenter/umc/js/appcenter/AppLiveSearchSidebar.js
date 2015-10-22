/*
 * Copyright 2013-2015 Univention GmbH
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
	"dojo/Deferred",
	"dojo/regexp",
	"dijit/form/Select",
	"umc/widgets/ContainerWidget",
	"umc/widgets/SearchBox",
	"umc/i18n!"
], function(declare, lang, array, has, Deferred, regexp, Select, ContainerWidget, SearchBox, _) {
	return declare("umc.modules.appcenter.AppLiveSearchSidebar", [ContainerWidget], {
		// summary:
		//		Offers a side bar for live searching, a set of categories can be defined.
		//		This class is used in the UMC overview and the App Center.

		// categories: Object[]|String[]
		//		Array of categories exposing at least the fields 'id' and 'label'
		//		or array of strings.
		categories: null,

		_categoriesAsIdLabelPairs: true,

		selectFormDeferred: null,

		// category: Object|String
		//		Reference to the currently selected category
		category: null,

		searchLabel: null,

		selectForm: null,

		_selectForm: null,

		baseClass: 'umcLiveSearchSidebar',

		// searchableAttributes: String[]
		//		Array of strings that shall be searched.
		//		defaults to ['name', 'description', 'categories', 'keywords']
		searchableAttributes: null,

		_lastValue: '',

		buildRendering: function() {
			this.selectFormDeferred = new Deferred();
			this.inherited(arguments);
			if (this.searchableAttributes === null) {
				this.searchableAttributes = ['name', 'description', 'categories', 'keywords'];
			}

			this.searchTextBox = new ContainerWidget({ 'class': 'umcSize-FourThirds searchField'});
			this._searchTextBox = new SearchBox({
				inlineLabel: this.searchLabel || _('Search term')
			});
			this.searchTextBox.addChild(this._searchTextBox);
			this.addChild(this.searchTextBox);

		},

		postCreate: function() {
			this.inherited(arguments);
			this._searchTextBox.on('keyup', lang.hitch(this, function() {
				if (this.get('value') || this._lastValue) {
					// ignore empty search strings
					this._lastValue = this.get('value');
					this.onSearch();
				}
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
			if (!this._categoriesAsIdLabelPairs) {
				return category.id;
			}
			return category;
		},

		_setCategoryAttr: function(_category) {
			var category = this._getUniformCategory(_category);
			this._set('category', category);
			var selectedChild = array.filter(this._selectForm._getChildren(), function(child) {
				return category.label === child.label;
			});
			this._selectForm.focusChild(selectedChild[0]);
			this.onSearch();
			this.onCategorySelected();
			if (!has('touch')) {
				this._searchTextBox.focus();
			}
		},

		_setCategoriesAttr: function(categories) {
			if (this._selectForm) {
				this._selectForm.removeOption(this._selectForm.getOptions());
			}
			this._set('categories', categories);

			var selectFormOptions = array.map(categories, lang.hitch(this, function(_category, idx) {
				var category = this._getUniformCategory(_category);
				return {
					label: category.label,
					value: category.label,
					_categoryID: category.id
				};
			}));
			
			if (this.selectForm) {
				this.removeChild(this.selectForm);
				this.selectForm.destroyRecursive();
				this.selectForm = null;
				this.selectFormDeferred = this.selectFormDeferred.isResolved() ? new Deferred() : this.selectFormDeferred;
			}
			this.selectForm = new ContainerWidget({'class': 'umcSize-TwoThirds dropDownMenu'});
			this._selectForm = new Select({
				options: selectFormOptions
			});
			this.selectFormDeferred.resolve();

			this._selectForm.watch('value', lang.hitch(this, function(attr, oldval, newval) {
				if (newval) {
					var selectedOption = this._selectForm.getOptions(newval);
					var selectedCategory = {id: selectedOption._categoryID, label: selectedOption.label};
					//this.set('value', '');
					this.set('category', selectedCategory);
				}
			}));
			this._selectForm.loadDropDown(function() {
				//empty callback for loading the SelectForm dropdown
			});
			this._selectForm.dropDown.set('class', 'AppLiveSearchSidebarDropDown');

			this.selectForm.addChild(this._selectForm);
			this.own(this.selectForm);
			this.addChild(this.selectForm);


			// preselect the first category
			this.set('category', categories[0]);
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
		},

		onCategorySelected: function() {
			//event stub
		}
	});
});

