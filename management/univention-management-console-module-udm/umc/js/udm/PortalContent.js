/*
 * Copyright 2018-2019 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/query",
	"dojo/aspect",
	"dojo/dnd/Source",
	"umc/widgets/MultiInput",
	"put-selector/put",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, domClass, domAttr, domStyle, query, aspect, Source, MultiInput, put, _) {
	return declare("umc.models.udm.PortalContent", [ MultiInput ], {
		// summary:
		//     For the display of the 'content' property of settings/portal objects.
		//     Allows nested MultiInputs with dojo/dnd

		baseClass: 'umcMultiInput',

		_updateNames: function() {
			var _this = this;
			array.forEach(this._widgets, function(rowWidgets, row) {
				array.forEach(rowWidgets, function(widget, x) {
					widget.name = '__' + _this.name + '-' + row + '-' + x;
					if (widget instanceof MultiInput) {
						widget._updateNames();
					}
				});
			});
		},

		updateAfterDnd: function() {
			var widgets = [];
			var rowContainers = [];
			var nRenderedElements = 0;
			array.forEach(this.dndSource.getAllNodes(), function(rowContainerNode, irow) {
				var rowContainer = dijit.byId(domAttr.get(rowContainerNode, 'widgetId'));
				rowContainer.irow = irow;
				widgets.push(rowContainer.visibleWidgets);
				rowContainers.push(rowContainer);
				nRenderedElements++;
			});
			this._widgets = widgets;
			this._updateNames();
			this._rowContainers = rowContainers;
			this._nRenderedElements = nRenderedElements;
			if (this._nRenderedElements === 0) {
				this._appendRows();
			}
			this._set('value', this.get('value'));
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.dndPlaceholderHideout = put(this.domNode, 'div.dndPlaceholderHideout');
			this.dndPlaceholder = put(this.dndPlaceholderHideout, 'div.dndPlaceholder');
			domClass.add(this.dndPlaceholder, lang.replace('dojoDndItem dojoDndItem_{0}', [this.dndOptions.accept[0]]));

			var properties = lang.mixin({
				withHandles: true,
				parentWidget: this
			}, this.dndOptions);

			this.dndSource = new Source(this.domNode, properties);
			domClass.add(this.domNode, lang.replace('dojoDndSource_{0}', [this.dndOptions.type[0]]));
			
			this.own(aspect.after(this.dndSource, 'onDropInternal', function(nodes, copy) {
				this.parentWidget.updateAfterDnd();
			}, true));
			this.own(aspect.after(this.dndSource, 'onDropExternal', function(source, nodes, copy) {
				this.parentWidget.updateAfterDnd();
				source.parentWidget.updateAfterDnd();
			}, true));

			this.own(aspect.after(this.dndSource, 'onDndStart', lang.hitch(this, function(source) {
				if (this.dndSource.type[0] === source.type[0]) {
					query('.dojoDndItem_dndCover', this.domNode).removeClass('dijitDisplayNone');
				}
			}), true));
			this.own(aspect.after(this.dndSource, 'onDndCancel', lang.hitch(this, function() {
				query('.dojoDndItem_dndCover', this.domNode).addClass('dijitDisplayNone');
			}), true));
		},

		validate: function() {
			var areValid = true;
			if (this.syntax === 'PortalCategorySelection') {
				var valid = [];
				var details = [];
				var i, j;
				for (i = 0; i < this._widgets.length; ++i) {
					if (this._widgets[i][0].get('value') == '' && this._widgets[i][1].get('value').length) {
						valid[i] = false;
						details[i] = _('A portal category has to be selected');
						areValid = false;
					} else {
						valid[i] = true;
						details[i] = '';
					}
				}
				if (!areValid) {
					this.setValid(valid, details);
				}
			}
			return areValid && this.inherited(arguments);
		},

		__appendRow: function(irow) {
			this.inherited(arguments);
			var rowContainer = this._rowContainers[irow];
			put(rowContainer.domNode, 'div.dojoDndHandle div.dojoDndHandle_icon');
			put(rowContainer.domNode, 'div.dojoDndItem_dndCover.dijitDisplayNone');
			domAttr.set(rowContainer.domNode, 'dndType', this.dndOptions.accept[0]);
			domClass.add(rowContainer.domNode, lang.replace('dojoDndItem dojoDndItem_{0}', [this.dndOptions.accept[0]]));
			this.dndSource.sync();
		}
	});
});
