/*
 * Copyright 2016-2018 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/query",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/widgets/ContainerWidget",
	"put-selector/put",
	"./PortalGallery",
	"umc/i18n!portal"
], function(declare, lang, on, domClass, domConstruct, domQuery, Memory, Observable, ContainerWidget, put, PortalGallery, _) {
	return declare("PortalCategory", [ContainerWidget], {
		baseClass: 'portalCategory',

		apps: null,

		heading: null,

		domainName: null,

		grid: null,

		query: null,

		_setQueryAttr: function(query) {
			this.grid.set('query', query);
			this._updateVisibility();
			this._set('query', query);
		},

		buildRendering: function() {
			this.inherited(arguments);

			// header
			var header = put(this.containerNode, 'h2', this.heading);
			if (!this.heading) {
				header.innerHTML = _('No display name provided');
				put(header, '.noDisplayNameProvided');
			}
			this.own(on(header, 'click', lang.hitch(this, function() {
				this.onEditCategory();
			})));

			// gallery
			var wrapper = put(this.containerNode, 'div.dojoDndItem_dndCoverWrapper');
			put(wrapper, 'div.dojoDndItem_dndCover.dijitDisplayNone');
			this.grid = new PortalGallery({
				store: new Observable(new Memory({
					data: this.apps
				})),
				domainName: this.domainName,
				category: this.category,
				useDnd: this.useDnd
			});
			put(wrapper, this.grid.domNode);
		},

		postCreate: function() {
			this._updateVisibility();
		},

		_updateVisibility: function() {
			var appsDisplayed = domQuery('div[class*="dgrid-row"]', this.grid.contentNode);
			var hideCategory = appsDisplayed.length === 0;
			domClass.toggle(this.domNode, 'dijitDisplayNone', hideCategory);
		},

		onEditCategory: function() {
			// event stub
		}
	});
});
