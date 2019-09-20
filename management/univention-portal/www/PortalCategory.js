/*
 * Copyright 2016-2019 Univention GmbH
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
/*global define*/

/**
 * @module portal/PortalCategory
 * @extends module:umc/widgets/ContainerWidget
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"dojo/on",
	"dojo/dom-class",
	"umc/widgets/ContainerWidget",
	"put-selector/put",
	"./PortalGallery",
	"./tools.js",
	"umc/i18n!portal"
], function(declare, lang, aspect, on, domClass, ContainerWidget, put, PortalGallery, portalTools, _) {
	return declare("PortalCategory", [ContainerWidget], /** @lends module:portal/PortalCategory# */ {
		baseClass: 'portalCategory',

		entries: null,

		heading: null,
		headingNode: null,

		domainName: null,

		grid: null,

		query: null,

		/**
		 * Passed to {@link module:portal/PortalGallery}.
		 * Refer to {@link module:portal/PortalGallery#defaultLinkTarget}.
		 * @type {?String}
         */
		defaultLinkTarget: null,

		_setQueryAttr: function(query) {
			domClass.remove(this.domNode, 'dijitDisplayNone'); // The category has to be visible so that this.grid._resizeItemNames() works
			this.grid.set('query', query);
			this._updateVisibility();
			this._set('query', query);
		},

		buildRendering: function() {
			this.inherited(arguments);

			// header
			var header = this.headingNode = put('h2', this.heading);
			put(this.containerNode, this.headingNode);
			if (!this.heading) {
				header.innerHTML = _('No display name provided');
				put(header, '.noDisplayNameProvided');
			}

			// gallery
			this.grid = new PortalGallery({
				entries: this.entries,
				domainName: this.domainName,
				category: this.category,
				renderMode: this.renderMode,
				defaultLinkTarget: this.defaultLinkTarget,
			});

			switch (this.renderMode) {
				case portalTools.RenderMode.NORMAL:
					this.addChild(this.grid);
					break;
				case portalTools.RenderMode.EDIT:
					this.addChild(this.grid);
					if (this.$notInPortalJSON$) {
						this.own(on(header, 'click', lang.hitch(this, function() {
							this.onCategoryNotInPortalJSON();
						})));
					} else {
						this.own(on(header, 'click', lang.hitch(this, function() {
							this.onEditCategory();
						})));
					}
					this.own(aspect.after(this.grid, 'onAddEntry', lang.hitch(this, function() {
						this.onAddEntry();
					})));
					this.own(aspect.after(this.grid, 'onEditEntry', lang.hitch(this, function(entry) {
						this.onEditEntry(entry);
					}), true));
					this.own(aspect.after(this.grid, 'onEntryNotInPortalJSON', lang.hitch(this, function(entry) {
						this.onEntryNotInPortalJSON(entry);
					}), true));
					break;
				case portalTools.RenderMode.DND:
					put(header, '.dojoDndHandle');
					put(this.containerNode, 'div.dojoDndItem_dndCoverWrapper div.dojoDndItem_dndCover.dijitDisplayNone +', this.grid.domNode);
					break;
			}
		},

		startup: function() {
			this.grid.startup();
			this._updateVisibility();
		},

		_updateVisibility: function() {
			var hideCategory;
			if (this.renderMode === portalTools.RenderMode.DND) {
				hideCategory = false;
			} else {
				var renderedApps = this.grid.store.query(this.grid.query, this.grid.queryOptions);
				hideCategory = renderedApps.length === 0;
			}
			this.set('visible', !hideCategory);
		},

		getRenderedTiles: function() {
			return this.grid.store.query(this.grid.query, this.grid.queryOptions);
		},

		onEditCategory: function() {
			// event stub
		},

		onEditEntry: function(entry) {
			// event stub
		},

		onAddEntry: function() {
			// event stub
		},

		onEntryNotInPortalJSON: function(entry) {
			// event stub
		},

		onCategoryNotInPortalJSON: function() {
			// event stub
		}
	});
});
