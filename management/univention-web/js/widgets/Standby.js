/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

