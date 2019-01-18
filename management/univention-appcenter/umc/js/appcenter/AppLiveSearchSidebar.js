/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/dom-construct",
	"dojo/regexp",
	"umc/widgets/CheckBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Form",
	"umc/widgets/SearchBox",
	"umc/i18n!"
], function(declare, lang, array, has, Deferred, domConstruct, regexp, CheckBox, ContainerWidget, Form, SearchBox, _) {
	return declare("umc.modules.appcenter.AppLiveSearchSidebar", [ContainerWidget], {
		// summary:
		//		Offers a side bar for live searching, a set of categories can be defined.

		// categories: Object[]|String[]
		//		Array of categories exposing at least the fields 'id' and 'label'
		//		or array of strings.
		categories: null,

		_categoriesAsIdLabelPairs: true,

		selectFormDeferred: null,

		// category: Object[]|String[]
		//		Array of the currently selected categories
		selectedCategories: [],

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

			this.selectedCategories = [];  // Reset this filter, when opening the App Center

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

		_setCategoriesAttr: function(categories) {
			if (this._selectForm) {
				this._selectForm.removeOption(this._selectForm.getOptions());
			}
			this._set('categories', categories);

			this._addCategorySelector(categories);
		},

		_addCategorySelector: function(categories) {
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
			this.selectForm = new ContainerWidget({'class': 'appLiveSearchSidebarElement'});
			domConstruct.create('span', {
				innerHTML: _('Categories'),
				'class': 'mainHeader'
			}, this.selectForm.domNode);

			var widgets = [];
			array.forEach(selectFormOptions, lang.hitch(this, function(category) {
				widgets.push({
					type: CheckBox,
					name: category.value,
					label: category.label,
					onChange: lang.hitch(this, function(arg) {
						if (arg == true) {
							this.selectedCategories.push(category.value);
						} else {
							this.selectedCategories = this.selectedCategories.filter(
								function(x) {return x != category.value;}
							);
						}
						this.onSearch();  // Trigger the refresh of the displayed Apps
					})
				});
			}));
			var form = new Form({
				widgets: widgets,
			});
			this.selectForm.addChild(form);

			this.selectFormDeferred.resolve();

			this.own(this.selectForm);
			this.addChild(this.selectForm);
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

