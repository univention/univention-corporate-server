/*
 * Copyright 2020-2021 Univention GmbH
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
	"dojo/on",
	"dojo/topic",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/tools",
	"umc/widgets/ToggleButton",
	"umc/widgets/Button",
	"umc/i18n!umc/modules/appcenter"
], function(
	declare, lang, array, domClass, on, topic, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin,
	tools, ToggleButton, Button, _
) {
	return declare('umc.modules.appcenter.Tiles', [
		_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin
	], {
		//// overwrites
		baseClass: 'umcTiles',
		templateString: `
			<div>
				<div class="umcTiles__header">
					<h2>\${header}</h2>
					<button
						class="ucsTextButton umcTiles__selectionToggleButton dijitDisplayNone"
						data-dojo-type="umc/widgets/ToggleButton"
						data-dojo-attach-point="_selectionModeToggleButton"
						data-dojo-props="
							label: this._selectionModeToggleButtonLabel,
							iconClass: 'check-square'
						"
					></button>
				</div>
				<div data-dojo-attach-point="_actionBarNode" class="umcTiles__actionBar dijitDisplayNone">
					<div class="umcTiles__actionBar__buttons">
						<button
							data-dojo-attach-point="_installButton"
							data-dojo-type="umc/widgets/Button"
							data-dojo-props="
								disabled: true,
								label: this._installButtonLabel,
							"
							class="ucsTextButton"
						></button>
					</div>
					<span data-dojo-attach-point="selectedNode" class="umcTiles__actionBar__text"></span>
				</div>
				<div class="umcTiles__collection" data-dojo-attach-point="containerNode"></div>
			</div>
		`,


		//// self
		tiles: null,
		_setTilesAttr: function(tiles) {
			array.forEach(this.tiles, lang.hitch(this, function(tile) {
				this.removeChild(tile);
				tile.destroy();
			}));
			tiles = array.filter(tiles, lang.hitch(this, function(tile) {
				return this.query(tile.obj);
			}));

			const appIds = tiles.map(tile => tile.obj.id);
			this._selection = this._selection.filter(appId => appIds.includes(appId));
			array.forEach(tiles, lang.hitch(this, function(tile) {
				if (this._selection.includes(tile.obj.id)) {
					domClass.add(tile.domNode, 'selected');
				}
				this.own(on(tile, 'click', lang.hitch(this, '_onTileClick', tile)));
				this.addChild(tile);
			}));

			this._set('tiles', tiles);
			this._updateSelectionNote();
			this._updateButtons();
			this.set('visible', !!tiles.length);
		},

		hasSelectionMode: true,
		_selectionModeToggleButtonLabel: _('Select'),
		_selection: null,
		_updateSelectionNote: function() {
			this.selectedNode.innerHTML = _('%s of %s Apps selected', this._selection.length, this.tiles.length);
		},
		_installButtonLabel: _('Install'),
		_updateButtons: function() {
			this._installButton.set('disabled', this._selection.length === 0);
		},
		_isInSelectionMode: false,

		_onTileClick: function(tile) {
			if (this._isInSelectionMode) {
				var appId = tile.obj.id;
				var idx = this._selection.indexOf(appId);
				if (idx === -1) {
					this._selection.push(appId);
					domClass.toggle(tile.domNode, 'selected', true);
				} else {
					this._selection.splice(idx, 1);
					domClass.toggle(tile.domNode, 'selected', false);
				}
				this._updateSelectionNote();
				this._updateButtons();
			} else {
				topic.publish('/appcenter/open', tile.obj, this.isSuggestionCategory);
			}
		},

		filter: function(filterF) {
			var anyVisible = false;
			array.forEach(this.tiles, function(tile) {
				var visible = filterF(tile.obj);
				anyVisible = anyVisible || visible;
				tile.set("visible", visible);
			});
			this.set('visible', anyVisible);
		},

		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		},


		//// lifecycle
		constructor: function() {
			this._selection = [];
		},

		postCreate: function() {
			this.inherited(arguments);
			tools.toggleVisibility(this._selectionModeToggleButton, this.hasSelectionMode);
			if (this.hasSelectionMode) {
				this._selectionModeToggleButton.watch('checked', (_attr, _oldVal, newVal) => {
					this.set('_isInSelectionMode', newVal);
					tools.toggleVisibility(this._actionBarNode, newVal);
					domClass.toggle(this.domNode, this.baseClass + '__selectionMode', newVal);
				});
				// do this here and not in the props for the togglebutton to trigger _actionBarNode visibility
				this._selectionModeToggleButton.set('checked', this._isInSelectionMode);
			}
		}
	});
});
