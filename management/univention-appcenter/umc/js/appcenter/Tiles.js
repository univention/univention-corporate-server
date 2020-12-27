/*
 * Copyright 2020 Univention GmbH
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

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_Widget",
	"dijit/_Container",
	"dijit/_TemplatedMixin"
], function(declare, lang, array, domClass, _Widget, _Container, _TemplatedMixin) {
	return declare("umc.modules.appcenter.Tiles", [_Widget, _Container, _TemplatedMixin], {
		tiles: null,
		baseClass: 'umcTiles',
		templateString: `
			<div>
				<h2>\${header}</h2>
				<div class="collection" data-dojo-attach-point="containerNode"></div>
			</div>
		`,
		_setTilesAttr: function(tiles) {
			array.forEach(this.tiles, function(tile) {
				this.removeChild(tile);
				tile.destroy();
			});
			tiles = array.filter(tiles, lang.hitch(this, function(tile) {
				return this.query(tile.obj);
			}));
			array.forEach(tiles, lang.hitch(this, function(tile) {
				tile.set("suggested", this.isSuggestionCategory);
				this.addChild(tile);
			}));
			this._set("tiles", tiles);
			this.set("visible", !!tiles.length);
		},
		filter: function(filterF) {
			array.forEach(this.tiles, function(tile) {
				var visible = filterF(tile.obj);
				tile.set("visible", visible);
			});
		},
		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		}
	});
});
