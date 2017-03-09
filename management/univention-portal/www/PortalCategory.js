/*
 * Copyright 2016-2017 Univention GmbH
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
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/query",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/widgets/ContainerWidget",
	"./PortalGallery",
], function(declare, domClass, domConstruct, domQuery, Memory, Observable, ContainerWidget, PortalGallery) {
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

			var heading = domConstruct.create("h2", {
				innerHTML: this.heading
			});

			var store = new Observable(new Memory({
				data: this.apps
			}));

			this.grid = new PortalGallery({
				store: store,
				domainName: this.domainName
			});

			domConstruct.place(heading, this.containerNode);
			this.addChild(this.grid);
		},

		postCreate: function() {
			this._updateVisibility();
		},

		_updateVisibility: function() {
			var appsDisplayed = domQuery('div[class*="dgrid-row"]', this.grid.contentNode);
			var hideCategory = appsDisplayed.length === 0;
			domClass.toggle(this.domNode, 'dijitDisplayNone', hideCategory);
		}
	});
});
