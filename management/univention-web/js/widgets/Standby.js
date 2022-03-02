/*
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/dom-style",
	"dojox/widget/Standby",
	"put-selector/put",
	"./StandbyCircle"
], function(declare, domStyle, Standby, put, StandbyCircle) {
	return declare("umc.widgets.Standby", [Standby], {
		centerIndicator: 'svg',
		duration: 200,
		opacity: 0.8,
		color: 'var(--bgc-content-body)',

		buildRendering: function() {
			this.inherited(arguments);
			this._svgNode = new StandbyCircle({}).domNode;
			domStyle.set(this._svgNode, {
				display: "none",
				opacity: "0",
				zIndex: -10000,
				position: "absolute",
				top: "0px",
				left: "0px",
				cursor: "wait"
			});
			put(this.domNode, this._svgNode);
		},

		startup: function() {
			this.inherited(arguments);
			if (this.centerIndicator === 'svg') {
				this._centerNode = this._svgNode;
			}
		},

		_setCenterIndicatorAttr: function(indicator) {
			this.centerIndicator = indicator;
			if(indicator === "image"){
				this._centerNode = this._imageNode;
				domStyle.set(this._textNode, "display", "none");
				domStyle.set(this._svgNode, "display", "none");
			} else if (indicator === "svg") {
				this._centerNode = this._svgNode;
				domStyle.set(this._imageNode, "display", "none");
				domStyle.set(this._textNode, "display", "none");
			} else {
				this._centerNode = this._textNode;
				domStyle.set(this._imageNode, "display", "none");
				domStyle.set(this._svgNode, "display", "none");
			}
		},

		uninitialize: function() {
			this.inherited(arguments);
			this._svgNode = null;
		}
	});
});

