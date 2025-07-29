/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define, window*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/on",
	"umc/widgets/Button",
	"put-selector/put",
], function(declare, array, lang, on, Button, put) {

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
			var bootstrapClasses = "col-xxs-12.col-xs-6.col-sm-6.col-md-4.col-lg-4";
			var wrapperDiv = put(lang.replace('div.umcGridTileWrapperItem.{bootstrapClasses}', {
				bootstrapClasses: bootstrapClasses
			}));
			var itemDiv = put(wrapperDiv, lang.replace('div.umcGridTileItem', item));
			if (this.grid._contextMenu) {
				var contextMenuButtonNode = Button.simpleIconButtonNode('more-horizontal', 'umcGridTileContextIcon');
				on(contextMenuButtonNode, "click", lang.hitch(this, function(evt) {
					evt.stopImmediatePropagation();
					this.grid._contextMenu._openMyself(evt);
				}));
				put(itemDiv, contextMenuButtonNode);
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

