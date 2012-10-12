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
	"dijit/registry",
	"umc/tools",
	"umc/widgets/Tooltip",
	"dgrid/OnDemandList",
	"dgrid/Selection",
	"put-selector/put"
], function(declare, lang, array, domClass, domStyle, registry, tools, Tooltip, List, Selection, put) {
	return declare("umc.widgets.GalleryPane", [ List, Selection ], {
		baseClass: "",

		style: "",

		categoriesDisplayed: true,

		_setStyleAttr: function(val) {
			this.inherited(arguments);
			console.log('dgrid set style:', val);
		},

		constructor: function() {
			this.id = registry.getUniqueId(this.declaredClass.replace(/\./g,"_"));
			registry.add(this);
		},

		destroy: function() {
			this.inherited(arguments);
			registry.remove(this.id);
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
			var div = put("div");
			div.innerHTML = lang.replace(
				'<div class="umcGalleryIcon {icon}"></div>' +
				'<div class="umcGalleryStatusIcon {status}"></div>' +
				'<div class="umcGalleryName">{name}</div>' +
				'<div class="umcGalleryDescription">{categories}</div>', {
					icon: this.getIconClass(item),
					status: this.getStatusIconClass(item),
					name: item.name,
					categories: this.categoriesDisplayed ? item.categories.join(', ') : ''
				}
			);
			domClass.add(div, 'umcGalleryItem');
			return div;
		},

		getIconClass: function(item) {
			return tools.getIconClass(item.icon, 50);
		},

		getStatusIconClass: function(item) {
			return '';
		},

		refresh: function() {
			this.inherited(arguments);
			this._addTooltips();
		},

		_addTooltips: function() {
			if (!this.store) {
				return;
			}
			array.forEach(this.store.query(), function(item) {
				var tooltip = new Tooltip({
					label: item.description,
					connectId: [ this.row(item).element ]
				});
			}, this);
		}
	});
});

