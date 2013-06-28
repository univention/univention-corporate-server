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
	"dojo/dom-class",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TextBox",
	"umc/widgets/LabelPane",
	"umc/widgets/Button",
	"umc/i18n!umc/branding,umc/app"
], function(declare, lang, array, domClass, ContainerWidget, TextBox, LabelPane, Button, _) {
	return declare("umc.widgets.LiveSearchSidebar", [ContainerWidget], {
		// summary:
		//		Offers a side bar for live searching, a set of categories can be defined.
		//		This class is used in the UMC overview and the App Center.

		// categories: Object[]
		// 		Array of categories exposing at least the fields 'id' and 'label'.
		categories: null,

		// category: Object
		//		Reference to the currently selected category
		category: null,

		style: 'overflow: auto;',

		buildRendering: function() {
			this.inherited(arguments);

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

		_isInSearchMode: function() {
			return Boolean(lang.trim(this.get('value')));
		},

		_getValueAttr: function() {
			return this._searchTextBox.get('value');
		},

		_getCategoryAll: function() {
			var result = array.filter(this.get('categories'), function(icat) {
				return icat && icat.id == '$all$';
			});
			if (result.length) {
				return result[0];
			}
			return null;
		},

		_getCategoryAttr: function() {
			if (this._isInSearchMode()) {
				// in search mode, the current category is always the "all" category
				return this._getCategoryAll();
			}
			return this.category;
		},

		_setCategoryAttr: function(category) {
			this._set('category', category);
			this._updateCss();
			this.onSearch();
		},

		_clearCategoryNodes: function() {
			array.forEach(this._categoryContainer.getChildren(), lang.hitch(this, function(category) {
				this._categoryContainer.removeChild(category);
				category.destroyRecursive();
			}));
		},

		_setCategoriesAttr: function(_categories) {
			this._clearCategoryNodes();

			// add new categories
			var categories = lang.clone(_categories);

			// add generic categories
			categories.unshift({
				label: _('All'),
				id: '$all$'
			});
			categories.unshift({
				label: _('Favorites'),
				id: '$favorites$'
			});

			// add one node elements for each category
			array.forEach(categories, lang.hitch(this, function(category) {
				this._categoryContainer.addChild(new Button({
					label: category.label,
					_categoryID: category.id,
					callback: lang.hitch(this, 'set', 'category', category)
				}));
			}));

			this._set('categories', categories);

			// preselect the first category
			this.set('category', categories[0]);
		},

		_updateCss: function() {
			var categories = this._categoryContainer.getChildren();
			var currentCategory = this.get('category');
			array.forEach(categories, lang.hitch(this, function(ibutton) {
				var isSelected = (currentCategory && currentCategory.id == ibutton._categoryID) || (!currentCategory && ibutton._categoryID == '$all$');
				domClass.toggle(ibutton.domNode, 'umcCategorySelected', isSelected);
			}));
		},

		focus: function() {
			this._searchTextBox.focus();
		},

		onSearch: function() {
			// event stub
		}
	});
});

