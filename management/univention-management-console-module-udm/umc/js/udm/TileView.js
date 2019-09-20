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
/*global define, window*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/on",
	"put-selector/put",
], function(declare, array, lang, on, put) {

	return declare("umc.module.udm.TileView", [], {

		baseClass: "umcGridTile",

		necessaryUdmValues: ["displayName", "mailPrimaryAddress", "firstname", "lastname"], 

		_queryTimer: null,

		_queryCache: null,

		_userImageNodes: {},

		grid: null,

		setPicture: function(item) {
			if (this._queryTimer) {
				this.grid.moduleStore.get(item.$dn$);
			} else {
				this._queryCache = this.grid.moduleStore.transaction();
				this._queryTimer = window.setTimeout(lang.hitch(this, "_setPictures"), 100);
				this.grid.moduleStore.get(item.$dn$);
			}
		},

		_setPictures: function() {
			this._queryTimer = null;
			this._queryCache.commit().then(lang.hitch(this, function(data) {
				array.forEach(data, function(item){
					if (item.jpegPhoto) {
						//put(this._userImageNodes[item.$dn$], "+img.umcGridTileIcon[src=data:image/jpeg;base64," + item.jpegPhoto + "]");
						put(this._userImageNodes[item.$dn$], "+div.umcGridTileIcon[style=background-image: url(data:image/jpeg;base64," + item.jpegPhoto + ")]");
					}
				}, this);
			}));
		},

		_getInitials: function(item) {
			var initials = "";
			// FIXME: item.firstname[0] is not unicode save!
			// eg: 𝐀 (\uD835\uDC00) is returned as \uD835
			// That should only be a problem for characters from the supplementary planes
			// https://github.com/mathiasbynens/String.prototype.at
			if (item.firstname) {
				initials += item.firstname[0];
			}
			if (item.lastname) {
				initials += item.lastname[0];
			}
			return initials;
		},

		_getDescription: function(item) {
			var description = put('div.umcGridTileDescription');
			if (item.displayName) {
				put(description, 'div', item.displayName);
			}
			if (item.mailPrimaryAddress) {
				put(description, 'div', item.mailPrimaryAddress);
			}
			put(description, 'div', item.path);
			return description;
		},


		renderRow: function(item) {
			var bootstrapClasses = "col-xxs-12.col-xs-6.col-sm-6.col-md-4.col-lg-3";
			var wrapperDiv = put(lang.replace('div.umcGridTileWrapperItem.{bootstrapClasses}', {
				bootstrapClasses: bootstrapClasses
			}));
			var itemDiv = put(wrapperDiv, lang.replace('div.umcGridTileItem', item));
			if (this.grid._contextMenu) {
				var contextMenu = put(itemDiv, 'div.umcGridTileContextIcon');
				on(contextMenu, "click", lang.hitch(this, function(evt) {
					evt.stopImmediatePropagation();
					this.grid._contextMenu._openMyself(evt);
				}));
			}
			this._userImageNodes[item.$dn$] = put(itemDiv, "div.umcGridTileIcon", this._getInitials(item));
			put(itemDiv, 'div.umcGridTileName', item.name);
			this.setPicture(item);
			put(itemDiv, this._getDescription(item));
			var defaultAction = this.grid._getDefaultActionForItem(item);
			var idProperty = this.grid.moduleStore.idProperty;
			on(itemDiv, 'click', lang.hitch(this, function(evt) {
				if (evt.ctrlKey) {
					return;
				}
				defaultAction.callback([item[idProperty]], [item]);
				var row = this.grid._grid.row(evt);
				this.grid._grid.deselect(row);
			}));
			return wrapperDiv;
		},
	});
});

