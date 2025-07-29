/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/widgets/Icon",
	"umc/menu/_ShowHideMixin",
	"umc/menu/Slide",
	"umc/tools"
], function(declare, lang, array, domClass, _WidgetBase, _TemplatedMixin, Icon, _ShowHideMixin, Slide, tools) {
	return declare('umc.menu.SubMenuItem', [_WidgetBase, _TemplatedMixin, _ShowHideMixin], {
		label: '',
		isSubMenu: true,
		priority: 0,
		parentSlide: null,

		templateString: '' +
			'<div data-dojo-attach-point="contentNode" class="menuItem popupMenuItem fullWidthTile">' +
				'${label}' +
				'<div data-dojo-attach-point="childItemsCounterNode" class="childItemsCounter"></div>' +
				Icon.asHTMLString('chevron-right', 'popupMenuItemArrow') +
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
