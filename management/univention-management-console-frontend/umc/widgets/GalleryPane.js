/*
 * Copyright 2012 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/dom-style",
	"dojo/dom-construct",
	"dijit/registry",
	"umc/tools",
	"umc/widgets/Tooltip",
	"umc/widgets/ContainerWidget",
	"dgrid/OnDemandList",
	"dgrid/Selection",
	"put-selector/put"
], function(declare, lang, array, domClass, domStyle, domConstruct, registry, tools, Tooltip, ContainerWidget, List, Selection, put) {
	return declare("umc.widgets.GalleryPane", [ List, Selection ], {
		baseClass: "",

		style: "",

		categoriesDisplayed: true,

		constructor: function() {
			this.id = registry.getUniqueId(this.declaredClass.replace(/\./g,"_"));
			registry.add(this);
			// really a container, no widget
			// is never shown, just keeps track of
			// all created tooltips and destroys them
			this._tooltipContainer = new ContainerWidget({});
		},

		destroy: function() {
			this.inherited(arguments);
			registry.remove(this.id);
			this._tooltipContainer.destroyRecursive();
		},

		postCreate: function() {
			this.inherited(arguments);

			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);

			// add specific DOM classes
			domClass.add(this.domNode, 'umcGalleryPane');
			if (this.baseClass) {
				domClass.add(this.domNode, this.baseClass);
			}

			// add specific CSS style given as string
			if (lang.isObject(this.style)){
				domStyle.set(this.domNode, this.style);
			}
			else {
				if (this.domNode.style.cssText){
					this.domNode.style.cssText += "; " + this.style;
				}
				else {
					this.domNode.style.cssText = this.style;
				}
			}

			// set the store
			if (this.store) {
				this.set('store', this.store);
			}
		},

		renderRow: function(item, options) {
			// create gallery item
			var div = put("div");
			var categories = this.categoriesDisplayed ? item.categories.join(', ') : '';
			domConstruct.create('div', {'class': 'umcGalleryIcon ' + this.getIconClass(item)}, div);
			var statusIconDiv = domConstruct.create('div', {'class': 'umcGalleryStatusIcon ' + this.getStatusIconClass(item)}, div);
			domConstruct.create('div', {'class': 'umcGalleryName', 'innerHTML': item.name}, div);
			domConstruct.create('div', {'class': 'umcGalleryDescription', 'innerHTML': categories}, div);
			domClass.add(div, 'umcGalleryItem');

			// Tooltip
			var tooltip = new Tooltip({
				label: item.description,
				connectId: [ div ]
			});
			this._tooltipContainer.own(tooltip);
			var statusIconLabel = this.getStatusIconTooltip(item);
			if (statusIconLabel) {
				var statusIconTooltip = new Tooltip({
					label: statusIconLabel,
					connectId: [ statusIconDiv ]
				});
				this._tooltipContainer.own(statusIconTooltip);
			}

			return div;
		},

		getIconClass: function(item) {
			return tools.getIconClass(item.icon, 50);
		},

		getStatusIconClass: function(item) {
			return '';
		},

		getStatusIconTooltip: function(item) {
			return '';
		}
	});
});

