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
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/menu/_ShowHideMixin",
	"umc/menu/Slide",
	"umc/tools"
], function(declare, lang, array, domClass, _WidgetBase, _TemplatedMixin, _ShowHideMixin, Slide, tools) {
	return declare('umc.menu.SubMenuItem', [_WidgetBase, _TemplatedMixin, _ShowHideMixin], {
		label: '',
		isSubMenu: true,
		priority: 0,
		parentSlide: null,

		templateString: '' +
			'<div data-dojo-attach-point="contentNode" class="menuItem popupMenuItem fullWidthTile">' +
				'${label}' +
				'<div data-dojo-attach-point="childItemsCounterNode" class="childItemsCounter"></div>' +
				'<div class="popupMenuItemArrow"></div>' +
				'<div class="popupMenuItemArrowActive"></div>' +
			'</div>',

		buildRendering: function() {
			this.inherited(arguments);
			this.menuSlide = new Slide({
				id: this.id + '__slide',
				label: this.label,
				isSubMenu: this.isSubMenu
			});
		},

		postCreate: function() {
			this.inherited(arguments);
			this.hide();
		},

		getMenuItems: function() {
			return this.menuSlide.itemsContainer.getChildren();
		},

		getVisibleMenuItems: function() {
			return array.filter(this.getMenuItems(), function(item) {
				return item.get('visible') && !item.isSeparator();
			});
		},

		addMenuItem: function(item) {
			// find the correct position for the entry
			var priorities = array.map(this.getMenuItems(), function(ichild) {
				return ichild.priority || 0;
			});
			var itemPriority = item.priority || 0;
			var pos = 0;
			for (; pos < priorities.length; ++pos) {
				if (itemPriority > priorities[pos]) {
					break;
				}
			}
			this.menuSlide.itemsContainer.addChild(item, pos);
			this._updateState();

			// update the counter if the 
			item.watch('visible', lang.hitch(this, '_updateState'));
		},

		_updateState: function() {
			var count = this.getVisibleMenuItems().length;
			this.childItemsCounterNode.innerHTML = count;
			this.set('visible', count > 0);
		},

		open: function(subMenuItem) {
			domClass.remove(this.menuSlide.domNode, 'hiddenSlide');
			domClass.add(this.domNode, 'menuItemActive menuItemActiveTransition');
			tools.defer(lang.hitch(this, function() {
				domClass.replace(this.parentSlide.domNode, 'overlappedSlide', 'topLevelSlide');
				domClass.add(this.menuSlide.domNode, 'visibleSlide topLevelSlide');
			}), 10);
		},

		close: function(subMenuItem) {
			domClass.remove(this.menuSlide.domNode, 'visibleSlide');
			domClass.remove(this.parentSlide.domNode, 'overlappedSlide');
			tools.defer(lang.hitch(this, function() {
				domClass.replace(this.menuSlide.domNode, 'hiddenSlide', 'topLevelSlide');
				domClass.add(this.parentSlide.domNode, 'topLevelSlide');
			}), 510);
			tools.defer(lang.hitch(this, function() {
				domClass.remove(this.domNode, 'menuItemActive');
				tools.defer(lang.hitch(this, function() {
					domClass.remove(this.domNode, 'menuItemActiveTransition');
				}), 400);
			}), 250);
		}
	});
});
