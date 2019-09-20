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
/*global define,require,console */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/has",
	"dojo/dom-class",
	"./LiveSearch",
	"./ContainerWidget",
	"./LabelPane",
	"./RadioButton",
	"umc/i18n!"
], function(declare, lang, array, has, domClass, LiveSearch, ContainerWidget, SearchBox, LabelPane, RadioButton, _) {
	return declare("umc.widgets.LiveSearchSidebar", [LiveSearch], {
		// !!!!!!!!!!!!!!!
		// This widget is broken! (dependencies do not match function parameters)
		//
		// At the moment it isn't used anywhere
		// !!!!!!!!!!!!!!!
		//
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

		collapsible: false,

		// category: Object|String
		//		Reference to the 'all' category
		allCategory: null,

		baseClass: 'umcLiveSearchSidebar',

		_radioButtons: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._radioButtons = [];
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._categoryContainer = new ContainerWidget({
				'class': 'umcLiveSearchSidebarRadioButtonGroup'
			});
			this.addChild(this._categoryContainer);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._searchTextBox.on('keyup', lang.hitch(this, '_updateCss'));
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
			var category = this._getUniformCategory(_category);
			this._set('category', category);
			array.forEach(this.categories, function(_icat, idx) {
				var icat = this._getUniformCategory(_icat);
				if (icat.id == category.id) {
					this._radioButtons[idx].set('checked', true);
				}
			}, this);
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
			this._radioButtons = array.map(categories, lang.hitch(this, function(_category, idx) {
				var category = this._getUniformCategory(_category);
				var radioButton = new RadioButton({
					label: category.label,
					value: category.label,
					checked: idx === 0,
					radioButtonGroup: this.id + '-group',
					_categoryID: category.id
					/*callback: lang.hitch(this, function() {
						this.set('value', '');
						this.set('category', category);
					})*/
				});
				radioButton.watch('checked', lang.hitch(this, function(attr, oldval, newval) {
					if (newval) {
						this.set('value', '');
						this.set('category', category);
					}
				}));
				var labelPane = new LabelPane({
					content: radioButton,
					// on small screens the navigation is displayed on top
					// of the main content
					'class': 'col-xs-6 col-md-12'
				});
				this._categoryContainer.addChild(labelPane);

				return radioButton;
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
		}
	});
});

